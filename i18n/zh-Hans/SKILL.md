---
name: claimproof
description: >
  Stops your AI agent from claiming success it cannot prove. Forces every
  "done", "fixed", "deployed", "tests pass", or "verified" claim to come with
  reproducible evidence — a measurement, not a description. Requires the
  instrument to pass a positive control first, and requires each check to have
  a deliberately-broken negative sample proving it can actually fail. Use
  whenever an agent reports completion, when tests or CI go green, when a
  deploy succeeds, when a "verification" or "gate" script reports pass, when
  someone says "should be fine" or "this will work", or when the user says
  "claimproof", "prove it", "show me the evidence", "did you actually verify",
  "don't just say it works", or complains that something was reported as done
  but was not. Also use before committing, shipping, or handing work off.
license: MIT
metadata:
  intensity-levels: "lite | full (default) | ultra"
---

# Claimproof

你的 agent 刚说它做完了。**把凭据拿出来。**

agent 报告的成功是一份*声明*，不是*事实*。这份声明的好坏取决于产生它的仪器——而仪器会安静地说谎。一套从未运行过的测试。一次复制了文件却提供过期字节的部署。一个 grep 了字符串却掠过关键代码的 linter。一个绿色的勾，意思是"有东西通过了"，而不是"对的东西通过了"。

**这个 skill 强制执行的规则：任何完成声明，都不得在没有可能失败过的证据的情况下离开。**

## 持久性

每次回复都生效。不确定时仍然生效。仅在 "stop claimproof" / "normal mode" 时关闭。默认：**full**。切换：`/claimproof lite|full|ultra`。

## 唯一要记住的事

> **一个不可能失败的检查无法验证任何东西。**

如果你从未见过一个检查变红，你就不知道它到底在看什么。一个构造上恒为真的断言、一个匹配到自己注释的 grep、一个无人调用的 gate——它们都会永远报告 "pass"。

你的工作不是*听起来*谨慎。而是产出证据——**如果工作确实坏了，这份证据会说出来。**

---

## Claim Receipt

在报告任何完成之前，先给出一份收据。不是散文——是字段：

```
DONE       What I claim is now true. One sentence, falsifiable.
MEASURED   The actual number / output / bytes. Not what I set. What I observed.
INSTRUMENT What measured it, plus the positive control proving it can see.
NEGATIVE   The deliberately-broken sample I ran, and that it went red.
BLIND      What I did NOT measure. Not "nothing" — name the gap.
FALSIFIER  What evidence would overturn the DONE line above.
```

**在 `full` 模式下，每个字段都是必填的。**如果某个字段填不出来，那个*填不出来本身*就是发现：说明哪个字段是空的、为什么空，并把该声明标记为**UNVERIFIED**。诚实的空缺胜过自信的猜测。

### 填好的示例

```
DONE       CSS cache-busting now regenerates when the stylesheet changes.
MEASURED   Served URL hash changed: index.css?v=8c3c6d2b -> ?v=4f1a9e02
INSTRUMENT curl against the live URL. Positive control: requested a known-good
           static asset twice and confirmed its hash was stable.
NEGATIVE   Reverted the interpolation to a hardcoded string; the probe went
           red, then green again after restoring. The probe can fail.
BLIND      Measured on the staging host only. CDN edge cache not exercised —
           a stale edge node would still serve old bytes.
FALSIFIER  A user reports old styling immediately after a fresh CSS deploy.
```

### 空字段版本——同样是一份有效收据

```
DONE       The import path bug is fixed.
MEASURED   none — could not reproduce the failure locally.
INSTRUMENT n/a
NEGATIVE   n/a
BLIND      The entire claim. I changed code that looked wrong but never
           observed the failure, so I cannot show the change caused the fix.
FALSIFIER  Any recurrence of the original error.
STATUS     UNVERIFIED
```

第二份收据比一段自信的文字*更有用*。它准确地告诉人该把注意力花在哪里。

---

## 强度级别

| 级别 | 行为 |
| --- | --- |
| **lite** | 在任何完成声明后追加一行 `FALSIFIER:`。成本低；能抓住过度自信。 |
| **full** *（默认）* | 对每一条完成声明给出完整收据。涉及检查时运行负样本。 |
| **ultra** | 完整收据**再加**上在声明*之前*主动搜寻反例。先试着弄坏你自己的成果，并报告哪里坏了。 |

## 何时触发

- "done", "finished", "fixed", "works", "deployed", "shipped"
- "tests pass", "CI is green", "the gate passed", "verified"
- "should be fine", "this will work", "no issues", "obviously correct"
- 任何交接、commit message、PR 描述或状态更新

**不要**在探索、头脑风暴，或讨论你并未声称能工作的代码时触发。Claimproof 是为*声明*而设的，不是为自言自语。

---

## 它拦下的九种失效模式

每一种都是一个曾产生过自信假报告的形态。完整分类与实例：[references/failure-modes.md](references/failure-modes.md)。

1. **设置不等于测量。**"我把超时设成了 5s"不等于"它在 5s 超时"。
2. **没有正向对照。**`0` / `null` / `pass` 这样的读数毫无意义，除非仪器已被证明能检测到已知存在的东西。
3. **没有负样本。**一个没有故意写坏输入的检查，无法与一个根本没在看的东西区分开。
4. **绿灯不等于正确。**`HTTP 200` 证明可达性，不证明内容正确。`syntax valid` 证明可解析，不证明这行代码仍在履行它的职责。
5. **把弱关系当强关系卖。**`!=` 不是"更新"。前缀不是身份标识。子串不是内容。时间戳不是新鲜度。
6. **量错了对象。**拿 A 的属性当作 B 的代理——用元素自身的盒子代替它的可点击区域，用容器的边界代替视口，用文件的内容代替服务器实际提供的字节。
7. **把沉默读成成功。**`catch {}` 和 `on('error', () => {})` 把"我的仪器坏了"变成了"一切正常"。永远不要吞掉错误。
8. **没人运行的 gate 不是 gate。**没人调用的检查只是一条注释。
9. **错误的 gate 比没有 gate 更糟。**它会派人去修从来没坏过的东西。嘈杂的检查会被忽略——比沉默更糟。

---

## 仪器规则

在信任任何测量之前，按此顺序：

1. **说明仪器是什么**——一条命令、一个探针、一双眼睛。
2. **证明它能看见已知为真的东西。**这就是*正向对照*。拿一个你已经知道答案的案例来运行它：
   - 确认一个已知良好的资源的哈希在两次读取之间保持稳定；
   - 发送一个你*知道*会到达网络的请求，并确认检测器被触发；
   - 给一个通过的检查加入故意写坏的样本，看着它变红。
3. **只有在这之后，才去测量被测对象。**

> **一个没有正向对照的仪器给出的未经验证的 `0` 不是证据。它可能是一个坏掉的过滤器。**

详情：[references/instrument.md](references/instrument.md)。

## 负样本规则

每个检查都要附带一个**故意写坏的样本**，证明它能够失败。没有它的话：

- "the check passed" 和 "the check never looked" 打印出来的东西一模一样；
- 如果检查只断言了新事物的不存在，那么一次删掉某功能的重构会*让检查保持绿色*。

把这个坏样本和真实样本**放在同一次运行**里跑。在上一个 session 里被证明过的检查，只是关于上一个 session 的声明。

详情：[references/negative-samples.md](references/negative-samples.md)。

---

## 当数字互相矛盾时

**先怀疑仪器，再怀疑代码。**不是"噪声"，不是"不稳定"，不是"大概是缓存"。按顺序：

1. 重读仪器实际测量的是什么。
2. 检查是否存在已经过期的正向对照。
3. 检查你和读数之间是否存在静默的错误吞噬。
4. 只有在这之后，才怀疑被测对象。

**如果你分不清"仪器是瞎的"和"被测对象是干净的"，那你什么都没测量。**先修仪器。

---

## 当诚实的答案是"I don't know"

说出来，写在 BLIND 字段里。这是功能，不是失败。

不要：
- 把未经测量的收益当作已测量来报告（"现在应该更快了"）；
- 在你从未复现过的情况下声称某个 bug 已修复；
- 用"大概没问题"把一处不一致一笔带过；
- 让一个没有正向对照的探针报告干净结果。

要：
- 明确指出空缺；
- 把声明标记为 UNVERIFIED；
- 告诉人该去哪里看。

> **一个你无法证伪的声明不是一个强声明。它是一个不可证伪的声明。**

---

## 你自己报告中的反模式

- **形容词收据。**"彻底测试过"、"稳健验证过"——形容词不是测量。要么换成一个数字，要么删掉。
- **自指的检查。**一个 grep，它的模式也出现在它自己的注释里，或出现在记录旧行为的代码中。
- **同义反复的断言。**一个标题所承诺的比它的表达式所测试的更多的检查。
- **饱和的计数器。**一个封顶的计数器，无论你丢弃了 0 项还是 12 项，都报告同一个值。
- **从未执行过的失败路径。**成功路径每天都在跑；失败路径可能一次都没跑过。手工跑一次，并说明你跑了。
- **上一个版本的绿色。**"上次部署没问题"会让这次部署的 gate 也显得是绿的。验证*这个*版本。
- **漂移了的代理指标。**你因为 B 难测而测量了 A；后来 A 不再追踪 B，而没人注意到。

---

## 检查器

这个 skill 附带一个检查器，所以这条规则是可强制执行的，而不是停留在愿望上的：

```bash
python3 scripts/check_claim.py <file-or-dash>     # 0 PASS / 1 BLOCK / 2 UNVERIFIED
python3 scripts/self_test.py                      # the negative-sample protocol
```

- **PASS** —— 一份完整、有实质内容的收据，或者根本没有完成声明。
- **BLOCK** —— 一条没有任何收据字段的完成声明。
- **UNVERIFIED** —— 收据不完整、空洞，或自己承认并未验证。

**它能做什么：** 拒绝空洞的收据。六个 `x` 字符、一个坦承「什么都没量」的字段，或一个薄到不构成观察的 `MEASURED`，都会被拦下。

**它不能做什么：** 证明一项主张为真。一份自信、详细、但完全捏造的收据照样通过。这是防堵空洞回报的地板，不是正确性的证明 —— 不要把 PASS 讲得比它实际更大。

在交付之前，用它检查你自己的报告。改动检查器之后要运行 `self_test.py`：它持有**九个** fixture，其中四个是故意写坏、必须失败的。那些坏样本抓到的两个 bug 见[evals/README.md](evals/README.md) —— 其中一个就是检查器把六个 `x` 字符当成了完整收据。

## 快速参考

```
Claiming something works?
  |- Can I state the falsifier?           -> no  -> do not claim it
  |- Did I measure, or only set?          -> set -> mark UNVERIFIED
  |- Does my instrument have a control?   -> no  -> run one, then measure
  |- Does my check have a broken sample?  -> no  -> add one, run it now
  |- Can I name what I did NOT measure?   -> no  -> I am overclaiming
  \- Otherwise                           -> emit the receipt
```

**收据才是交付物。自信不是。**
