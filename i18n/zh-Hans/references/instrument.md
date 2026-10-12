# 仪器规则

一次测量有多可信，取决于产生它的那个设备。本文档定义了什么才算一次可信的读数。

## 目录

- [1. 什么算作仪器](#1-what-counts-as-an-instrument)
- [2. 正向对照](#2-the-positive-control)
- [3. 为什么光秃秃的零什么都证明不了](#3-why-a-bare-zero-proves-nothing)
- [4. 仪器故障的特征](#4-instrument-failure-signatures)
- [5. 什么时候该怀疑干净的结果](#5-when-to-distrust-a-clean-result)
- [6. 完整流程示范](#6-worked-protocol)

---

## 1. 什么算作仪器

任何会产生一个你打算依赖的读数的东西：

- 一条 shell 命令（`curl`、`grep`、`md5sum`）
- 一个测试运行器或 linter
- 浏览器或测试框架里的一个探针
- 一个监视器、一份日志、一块仪表盘
- **你自己看截图的那双眼睛**

给仪器命名很重要，因为其中每一个都可能是瞎的。"它什么都没返回"是一句关于仪器的话，然后才是一句关于世界的话。

## 2. 正向对照

**正向对照是一个你已经知道答案的案例，用同一个仪器、在同一个 session 里跑一遍。**

它回答一个问题：*这个仪器到底能不能看见那个东西？*

| 情形 | 正向对照 |
| --- | --- |
| 检查没有流量离开这台机器 | 发送一个你*知道*会到达网络的请求；确认检测器被触发 |
| 检查某条 CSS 规则已经不在了 | 搜索一个你*知道*存在的字符串；确认命中数非零 |
| 检查页面能渲染 | 加载一个带有*已知*可见元素的页面；确认你的探针能找到它 |
| 检查一次部署提供了新字节 | 请求一个未改动的资源；确认它的哈希在两次读取之间保持稳定 |
| 检查某个 gate 能够失败 | 喂给它一个故意写坏的输入；确认它变红 |

没有正向对照，一个干净的读数有两种无法区分的原因：

1. 被测对象是干净的，或者
2. **仪器是瞎的。**

你无法根据一个你无法解读的读数行动。

## 3. 为什么光秃秃的零什么都证明不了

`0`、`null`、`empty` 或 `pass` 这样的读数是一个仪器能产生的最危险的输出，因为坏掉的仪器产生的也正是这个。

> **未经证实的零不是证据。它可能是一个坏掉的过滤器。**

这是自信的假报告诞生的最常见方式，没有之一。完整的模式列表在[failure-modes.md](failure-modes.md)；模式 2 和模式 7 就是这个东西换了身衣服。

## 4. 仪器故障的特征

记住这些。它们看起来都像好消息。

| 特征 | 它通常意味着 |
| --- | --- |
| 一切都失败，包括不可能失败的东西 | 坏的是仪器，不是被测对象 |
| 一次本该产生大量观察的运行却零观察 | 某个过滤器、端口或路径错了 |
| 一个在多次运行之间从不变化的读数 | 探针读的是某个恒定的东西，不是被测对象 |
| 在有效输入和坏输入上得到同一个值 | 这个断言构造上恒为真 |
| 一个在慢操作上瞬间返回的通过 | 工作被跳过了 |
| 一个关于连接、文件或不稳定的错误 | 在相信这个诊断之前，先检查仪器 |

## 5. 什么时候该怀疑干净的结果

只要出现下列情况，就怀疑干净的结果——并且去跑一个正向对照：

- 它来得比预期快；
- 它和人的报告矛盾；
- 最近没人见过这个检查失败；
- 这是这个检查第一次针对这个版本运行；
- 被测对象变了，但读数没变；
- 这个仪器最近被你或某个 agent 改过。

最后一条值得单独成为一条规则：**当你改动了仪器，你并没有改动被测对象。在读结果之前，先重新建立对照。**五分钟前被改过的探针，是一个未经校验的探针。

## 6. 完整流程示范

对你打算报告结果的任何测量，都套用这个形状。

```
CLAIM      (what you intend to conclude)

1. INSTRUMENT  name the exact command / probe.
2. CONTROL     run it on a case whose answer is already known;
               record the reading AND that it matched the known answer.
3. SUBJECT     run it on the thing under test.
4. NEGATIVE    if a check is involved, feed a deliberately-broken sample
               and confirm it is rejected.
5. GAP         state what this instrument cannot see.
```

### 具体例子

声明：*"前端不再调用生产环境端点了。"*

```
INSTRUMENT  packet capture on the container interface, filtered to the endpoint IP
CONTROL     request the endpoint directly -> capture shows the packets
            (proves the capture can see this traffic at all)
SUBJECT     drive the frontend -> capture shows 0 packets
NEGATIVE    point config at the endpoint temporarily -> packets appear again
            (proves the 0 came from the config, not from the filter)
GAP         covers IPv4 on this interface only; an IPv6 path or a proxy would
            be invisible to this capture
```

现在看看没有对照的版本——而大多数报告实际包含的正是这个：

```
INSTRUMENT  packet capture
SUBJECT     drove the frontend -> 0 packets -> "no traffic left the machine"
```

第二个版本不是更弱的证据。它**根本不是证据**——如果过滤器错了、网卡接口错了，或者流量只是走了一条过滤器从未看过的路，同样的输出都会出现。

---

## 两条规则

1. **在仪器被证明能检测到一个已知存在的东西之前，任何读数都不可信。**
2. **没有正向对照的零不是证据。**

这两条规则存在，是因为仪器会静默地、自信地失败。没有人会报告说自己的探针坏了——他们报告的是*系统*是干净的。
