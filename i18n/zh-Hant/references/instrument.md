# 儀器規則

一項量測的可信度，取決於產生它的裝置。本文件定義：要信任一個讀數，需要什麼條件。

## 目錄

- [1. 什麼算是一台儀器](#1-什麼算是一台儀器)
- [2. 正向對照](#2-正向對照)
- [3. 為什麼一個光禿禿的零證明不了任何事](#3-為什麼一個光禿禿的零證明不了任何事)
- [4. 儀器故障的特徵](#4-儀器故障的特徵)
- [5. 什麼時候該懷疑乾淨的結果](#5-什麼時候該懷疑乾淨的結果)
- [6. 完整協定範例](#6-完整協定範例)

---

## 1. 什麼算是一台儀器

任何會產生一個你打算據以行動的讀數的東西：

- 一個 shell 指令（`curl`、`grep`、`md5sum`）
- 一個測試執行器或 linter
- 瀏覽器或測試框架裡的一支探針
- 一個監控、一份日誌、一個儀表板
- **你自己的眼睛看著一張截圖**

指名儀器很重要，因為它們每一個都可能是瞎的。「它什麼都沒回傳」是一句關於儀器的陳述，然後才是一句關於世界的陳述。

## 2. 正向對照

**正向對照是一個你已經知道答案的案例，在同一個 session 中、跑過同一台儀器。**

它只回答一個問題：*這台儀器到底看不看得見那個東西？*

| 情境 | 正向對照 |
| --- | --- |
| 檢查沒有任何流量離開這台機器 | 送出一個你*知道*會上網路的請求；確認偵測器有反應 |
| 檢查某條 CSS 規則已經移除 | 搜尋一個你*知道*存在的字串；確認命中數非零 |
| 檢查頁面能正確渲染 | 載入一個帶有*已知*可見元素的頁面；確認你的探針找得到它 |
| 檢查一次部署送出了新的位元組 | 請求一個未變動的資源；確認它的雜湊在兩次讀取之間穩定 |
| 檢查一個閘門能失敗 | 餵給它一個故意寫壞的輸入；確認它變紅 |

少了正向對照，一個乾淨的讀數有兩個無法區分的原因：

1. 受測對象是乾淨的，或者
2. **儀器是瞎的。**

你無法依據一個你無法解讀的讀數行動。

## 3. 為什麼一個光禿禿的零證明不了任何事

讀數是 `0`、`null`、`empty` 或 `pass`，是一台儀器能產出的最危險的輸出，因為那也正是一台壞掉的儀器會產出的東西。

> **一個未經查證的零，不是證據。它是一個可能壞掉的濾網。**

這是自信的假報告被誕生出來最常見的單一途徑。完整的模式清單在 [failure-modes.md](failure-modes.md)；模式 2 與模式 7 就是這個東西換了件衣服。

## 4. 儀器故障的特徵

把這些記起來。它們看起來全都像是好消息。

| 特徵 | 它通常代表什麼 |
| --- | --- |
| 全部失敗，包括那些不可能失敗的東西 | 壞的是儀器，不是受測對象 |
| 一次理應產生大量觀察的執行，卻是零觀察 | 濾網、埠或路徑有錯 |
| 一個跨多次執行從不變動的讀數 | 探針讀的是某個恆定的東西，不是受測對象 |
| 在有效輸入與壞掉的輸入上得到同一個值 | 這個斷言在構造上恆為真 |
| 一個在緩慢操作上卻瞬間回傳的 pass | 工作被跳過了 |
| 一個關於連線、檔案或「不穩定」的錯誤 | 先檢查儀器，再相信這個診斷 |

## 5. 什麼時候該懷疑乾淨的結果

當下列情況發生時，懷疑一個乾淨的結果——並去跑一次正向對照：

- 它比預期更快抵達；
- 它與人類的回報矛盾；
- 最近沒有人見過這個檢查失敗；
- 這是這個檢查第一次跑在這一版上；
- 受測對象變了，但讀數沒變；
- 這台儀器最近被你自己或某個 agent 改過。

最後一項值得有自己的規則：**當你改動儀器時，你並沒有改動受測對象。在你讀取結果之前，重新建立對照。** 一支五分鐘前才被編輯過的探針，就是一支未經驗證的探針。

## 6. 完整協定範例

對任何你打算回報結果的量測，都使用這個形狀。

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

### 具體範例

宣稱：*「前端不再呼叫正式環境的 endpoint。」*

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

現在看沒有對照的版本——也就是大多數報告實際上包含的內容：

```
INSTRUMENT  packet capture
SUBJECT     drove the frontend -> 0 packets -> "no traffic left the machine"
```

第二個版本不是比較弱的證據。它**根本不是證據**——同樣的輸出也會在濾網錯了、介面錯了，或流量只是走了濾網從未看過的路徑時出現。

---

## 兩條規則

1. **在儀器被證明能偵測到一個已知存在的東西之前，任何讀數都不被信任。**
2. **一個沒有正向對照的零，不是證據。**

兩條規則之所以存在，是因為儀器會安靜又自信地故障。沒有人會回報自己的探針壞了——他們回報的是*系統*很乾淨。
