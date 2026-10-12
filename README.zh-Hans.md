# Claimproof

> **让你的 AI agent 不再宣称它证明不了的成果。**

agent 回报「成功」是一项*主张*，不是*事实*。Claimproof 强制每一个
「完成了」「修好了」「已部署」「测试通过」「已验证」都必须附上可重现的证据
—— 是一笔量测，不是一段描述。

## 问题

agent 会自信地、但错误地回报成功。不是因为它说谎，而是因为它的仪器在安静
地说谎：

- 从未真正被执行过的测试套件；
- 复制了文件、却仍旧送出过期字节的部署；
- 用字符串搜索扫过去、却错过真正关键代码的检查工具；
- 一个绿灯，代表的是「有东西通过了」，而不是「对的东西通过了」。

现有的验证工具都在问 **「这是真的吗？」**。Claimproof 问的是另一个问题：
**「这项主张有可能失败吗？如果不可能，你就什么都没验证到。」**

## 它做什么

在回报完成之前，agent 必须输出一张 **Claim Receipt（主张收据）**：

```
DONE       What I claim is now true. One sentence, falsifiable.
MEASURED   The actual number / output / bytes. Not what I set. What I observed.
INSTRUMENT What measured it, plus the positive control proving it can see.
NEGATIVE   The deliberately-broken sample I ran, and that it went red.
BLIND      What I did NOT measure. Not "nothing" — name the gap.
FALSIFIER  What evidence would overturn the DONE line above.
```

如果某个字段填不出来，**那本身就是发现** —— 该主张标记为 `UNVERIFIED`，
而不是被当成成功回报。

## 安装

```bash
# user level (available in every project)
cp -r claimproof ~/.dsh/skills/claimproof

# or project level
cp -r claimproof <your-project>/.dsh/skills/claimproof
```

DSH 会从文件系统自动探索 skill —— 不需要重启。

## 检查器

```bash
python3 scripts/check_claim.py report.md   # 0 PASS / 1 BLOCK / 2 UNVERIFIED
python3 scripts/self_test.py               # the negative-sample protocol
```

**它能做什么：** 拒绝空洞的收据。六个 `x` 字符、一个坦承「什么都没量」的
字段、或一个薄到不构成观察的 `MEASURED`，都会被拦下。

**它不能做什么：** 证明一项主张为真。一份自信、详细、但完全捏造的收据照样
通过。这是防堵空洞回报的地板，不是正确性的证明。不要把 PASS 讲得比它实际
更大。

检查器本身也受它自己主张的规则约束。`self_test.py` 跑九个 fixture，其中四个是
**故意写坏、必须失败**的。

两个真实的 bug 就是这样被抓到的，都是靠故意写坏的样本：

- 字段正则表达式用了 `\s`，把下一行吸收成自己的值，导致空白的 `MEASURED` 字段
  回报 PASS；
- 第一版接受六个 `x` 字符当作完整收据 —— 这是对抗性审查发现的，它指出：
  一个任何人都无法让它失败的检查器，正是这个 skill 自己在警告的那件事。

详见 `evals/README.md`。

上面每一项检查 —— 两个自测与全部十组翻译配对 —— 都会在每次 push 时通过 `scripts/verify.py` 在 CI 执行。见 `.github/workflows/verify.yml`。

## 强度等级

| 等级 | 行为 |
| --- | --- |
| `lite` | 在任何完成主张后面加一行 `FALSIFIER:`。便宜，能拦下过度自信。 |
| `full` *（默认）* | 每次完成主张都输出完整收据；涉及检查时要跑负样本。 |
| `ultra` | 完整收据 **加上** 在宣称之前先主动寻找反例 —— 先试着弄坏自己的成果，并回报弄坏了什么。 |

## 翻译

| 语言 | README | Skill 与参考文件 |
| --- | --- | --- |
| English *（正典）* | [README.md](README.md) | [SKILL.md](SKILL.md)、[references/](references/) |
| 繁體中文 | [README.zh-Hant.md](README.zh-Hant.md) | [i18n/zh-Hant/](i18n/zh-Hant/) |
| 简体中文 | 本档 | [i18n/zh-Hans/](i18n/zh-Hans/) |

DSH 永远加载根目录的 `SKILL.md`。`i18n/` 下面的文件深度不够，不会被
探索成 skill，因此永远不会造成触发歧义。翻译政策与「如何检测漏译」见
[i18n/README.md](i18n/README.md)。

翻译的漏译内容由 `scripts/check_translations.py` 检查，它比对结构、数字与代码
区块 —— 而它自己的自测证明了它会失败。

## 项目结构

```
claimproof/
├── SKILL.md                       the skill itself (English, canonical)
├── README.md                      English
├── README.zh-Hant.md              繁體中文
├── README.zh-Hans.md              简体中文
├── LICENSE                        MIT
├── references/
│   ├── failure-modes.md           the nine shapes of a false report
│   ├── instrument.md              positive controls and why zeros prove nothing
│   └── negative-samples.md        the four-state protocol
├── scripts/
│   ├── check_claim.py             receipt checker
│   ├── self_test.py               nine-fixture regression protocol
│   └── check_translations.py      proves a translation dropped nothing
├── evals/
│   ├── README.md                  incl. the bugs the negative samples caught
│   └── fixtures/                  one fixture per state
└── i18n/
    ├── README.md                  translation policy
    ├── zh-Hant/                   繁體版 skill 與參考文件
    └── zh-Hans/                   简体版 skill 与参考文件
```

## 唯一的一条规则

> **不会失败的检查，等于没有检查。**

如果你从来没看过某个检查变红，你就不会知道它到底有没有在看。

## 授权

MIT
