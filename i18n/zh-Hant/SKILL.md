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

你的 agent 剛才說它做完了。**要求它拿出收據。**

agent 回報成功，那是一則*宣稱*，不是*事實*。宣稱的品質，取決於產生它的儀器——而儀器會安靜地說謊。一套從未跑過的測試。一次複製了檔案、卻送出過期位元組的部署。一個用 grep 找到字串、卻走過真正重要程式碼的 linter。一個綠燈，代表的是「有東西通過了」，而不是「對的東西通過了」。

**這個 skill 強制執行的規則：任何完成宣稱，都必須附上一個「有可能失敗」的證據，才能離開。**

## 持續生效

每一次回應都生效。不確定時仍然生效。只有在說 "stop claimproof" / "normal mode" 時關閉。預設：**full**。切換：`/claimproof lite|full|ultra`。

## 唯一要記住的一件事

> **一個不可能失敗的檢查，無法驗證任何事。**

如果你從未見過一個檢查變紅，你就不知道它到底有沒有在看。一個在構造上恆為真的斷言、一個會 match 到自己註解的 grep、一個沒有任何東西呼叫的閘門——它們全都會永遠回報「pass」。

你的工作不是*聽起來*很小心，而是產出這樣的證據：**如果這份工作壞了，它會出聲指認。**

---

## Claim Receipt 收據

在回報任何完成之前，先產出一份收據。不是散文——是欄位：

```
DONE       What I claim is now true. One sentence, falsifiable.
MEASURED   The actual number / output / bytes. Not what I set. What I observed.
INSTRUMENT What measured it, plus the positive control proving it can see.
NEGATIVE   The deliberately-broken sample I ran, and that it went red.
BLIND      What I did NOT measure. Not "nothing" — name the gap.
FALSIFIER  What evidence would overturn the DONE line above.
```

**在 `full` 模式下，每個欄位都是必填。** 如果某個欄位填不出來，那*就是*發現：說出哪個欄位是空的、為什麼，並把這則宣稱標為 **UNVERIFIED**。誠實的空缺勝過自信的猜測。

### 填好的範例

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

### 空欄位的版本——同樣是一份有效收據

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

第二份收據比一段自信的文字*更有用*。它明確告訴人類，注意力該放在哪裡。

---

## 強度等級

| 等級 | 行為 |
| --- | --- |
| **lite** | 在任何完成宣稱後附加一行 `FALSIFIER:`。成本低；能抓到過度自信。 |
| **full** *（預設）* | 每個完成宣稱都附完整收據。涉及檢查時，跑負向樣本。 |
| **ultra** | 完整收據**加上**在宣稱*之前*主動獵捕反例。先試著弄壞你自己的成果，並回報什麼壞了。 |

## 何時觸發

- "done", "finished", "fixed", "works", "deployed", "shipped"
- "tests pass", "CI is green", "the gate passed", "verified"
- "should be fine", "this will work", "no issues", "obviously correct"
- 任何交接、commit 訊息、PR 描述或狀態更新

**不要**在探索、腦力激盪、或討論你並未宣稱能動的程式碼時觸發。Claimproof 是為*宣稱*而存在的，不是為自言自語。

---

## 它阻擋的九種失敗模式

每一種都曾產出過自信的假報告。完整分類與實例：[references/failure-modes.md](references/failure-modes.md)。

1. **設定不等於量測。** 「我把 timeout 設成 5s」不等於「它在 5s 時 timeout」。
2. **沒有正向對照。** 讀數是 `0` / `null` / `pass` 時，除非先證明儀器能偵測到已知存在的東西，否則毫無意義。
3. **沒有負向樣本。** 一個沒有故意寫壞輸入的檢查，與一個根本沒在看的檢查，無法區分。
4. **綠燈不等於正確。** `HTTP 200` 證明的是可達性，不是內容正確。`syntax valid` 證明的是可解析，不是那一行還在發揮作用。
5. **弱關係當成強關係賣。** `!=` 不是「較新」。前綴不是身分。子字串不是內容。時間戳不是新鮮度。
6. **量錯對象。** 拿 A 的屬性當 B 的代理——元素的 box 而不是它的可點擊區域、容器的邊界而不是 viewport、檔案的內容而不是實際送出的位元組。
7. **把沉默讀成成功。** `catch {}` 和 `on('error', () => {})` 把「我的儀器壞了」變成「一切正常」。絕不吞掉錯誤。
8. **沒人跑的閘門不是閘門。** 沒有任何東西呼叫的檢查，就是一段註解。
9. **錯的閘門比沒有閘門更糟。** 它會叫人去修從來沒壞的東西。吵雜的檢查會被忽略——比沉默更糟。

---

## 儀器規則

在信任任何量測之前，依序：

1. **說出儀器是什麼**——一個指令、一支探針、一雙眼睛。
2. **證明它看得見已知為真的事物。** 這就是*正向對照*。拿它去跑一個你已經知道答案的案例：
   - 確認一個已知良好資源的雜湊在兩次讀取之間穩定；
   - 送一個你*知道*會到網路的請求，並確認偵測器有反應；
   - 對一個原本通過的檢查加入故意寫壞的樣本，看它變紅。
3. **然後才量測受測對象。**

> **一個沒有正向對照的 `0`，不是證據。它是一個可能壞掉的濾網。**

細節：[references/instrument.md](references/instrument.md)。

## 負向樣本規則

每個檢查都隨附一個**故意寫壞的樣本**，證明它會失敗。少了它：

- 「檢查通過了」與「檢查根本沒在看」印出來一模一樣；
- 一個移除某功能的重構會*讓檢查保持綠色*，如果那個檢查只斷言了新東西的不存在。

把壞樣本**與真實案例在同一次執行中**一起跑。上一個 session 證明過的檢查，是關於上一個 session 的宣稱。

細節：[references/negative-samples.md](references/negative-samples.md)。

---

## 當數字對不上時

**先懷疑儀器，再懷疑程式碼。** 不是「雜訊」、不是「不穩定」、不是「大概是快取」。依序：

1. 重讀儀器實際量的是什麼。
2. 檢查正向對照是否已經過期。
3. 檢查你與讀數之間是否有被悄悄吞掉的錯誤。
4. 然後才懷疑受測對象。

**如果你分不出「儀器瞎了」與「受測對象是乾淨的」，你就什麼都沒量到。** 先修儀器。

---

## 當誠實的答案是「我不知道」時

說出來，寫在 BLIND 欄位。這是功能，不是失敗。

不要：
- 把未量測的好處講得像量過（「現在應該比較快」）；
- 在你從未重現過的情況下，宣稱某個 bug 修好了；
- 用「應該沒事」把一個不一致總結掉；
- 讓一支沒有正向對照的探針回報乾淨的結果。

要：
- 明確指名缺口；
- 把宣稱標為 UNVERIFIED；
- 告訴人類該去哪裡看。

> **一個你無法證偽的宣稱，不是強宣稱。它是一個不可證偽的宣稱。**

---

## 你自己回報時的反模式

- **形容詞收據。** 「徹底測試過」「穩健地驗證過」——形容詞不是量測。換成一個數字，或刪掉。
- **自我指涉的檢查。** 一個 grep，它的 pattern 也出現在自己的註解裡，或出現在記錄舊行為的程式碼裡。
- **套套邏輯的斷言。** 一個標題承諾得比它表達式實際測試的還多的檢查。
- **飽和的計數器。** 一個有上限的計數器，不管你漏掉 0 筆還是 12 筆，都回報同一個值。
- **從未被執行過的失敗路徑。** 成功路徑天天跑；失敗路徑可能從來沒跑過。手動跑它一次，然後說你跑過。
- **前一版的綠燈。** 「上次部署沒問題」會讓這次部署的閘門看起來也綠。驗證*這一版*。
- **漂移的代理。** 你因為 B 很難量而量了 A；後來 A 不再追蹤 B，卻沒有人發現。

---

## 檢查器

這個 skill 隨附一支檢查器，所以規則是可強制執行的，而不是理想而已：

```bash
python3 scripts/check_claim.py <file-or-dash>     # 0 PASS / 1 BLOCK / 2 UNVERIFIED
python3 scripts/self_test.py                      # the negative-sample protocol
```

- **PASS** —— 一份完整、有實質內容的收據，或者根本沒有完成宣稱。
- **BLOCK** —— 一個完全沒有收據欄位的完成宣稱。
- **UNVERIFIED** —— 收據不完整、空洞，或自己承認並未驗證。

**它能做什麼：** 拒絕空洞的收據。六個 `x` 字元、一個坦承「什麼都沒量」的欄位，或一個薄到不構成觀察的 `MEASURED`，都會被擋下。

**它不能做什麼：** 證明一項主張為真。一份自信、詳細、但完全捏造的收據照樣通過。這是防堵空洞回報的地板，不是正確性的證明 —— 不要把 PASS 講得比它實際更大。

在交接之前，拿它跑你自己的報告。改過檢查器之後要跑 `self_test.py`：它持有**九個** fixture，其中四個是故意寫壞、必須失敗的。那些壞樣本抓到的兩個 bug 見 [evals/README.md](evals/README.md) —— 其中一個是這支檢查器把六個 `x` 字元當成了完整收據。

## 快速參考

```
Claiming something works?
  |- Can I state the falsifier?           -> no  -> do not claim it
  |- Did I measure, or only set?          -> set -> mark UNVERIFIED
  |- Does my instrument have a control?   -> no  -> run one, then measure
  |- Does my check have a broken sample?  -> no  -> add one, run it now
  |- Can I name what I did NOT measure?   -> no  -> I am overclaiming
  \- Otherwise                           -> emit the receipt
```

**收據才是交付物。自信不是。**
