# Claimproof

> **讓你的 AI agent 不再宣稱它證明不了的成果。**

agent 回報「成功」是一項*主張*，不是*事實*。Claimproof 強制每一個
「完成了」「修好了」「已部署」「測試通過」「已驗證」都必須附上可重現的證據
—— 是一筆量測，不是一段描述。

## 問題

agent 會自信地、但錯誤地回報成功。不是因為它說謊，而是因為它的儀器在安靜
地說謊：

- 從未真正被執行過的測試套件；
- 複製了檔案、卻仍舊送出過期位元組的部署；
- 用字串搜尋掃過去、卻錯過真正關鍵程式碼的檢查工具；
- 一個綠燈，代表的是「有東西通過了」，而不是「對的東西通過了」。

現有的驗證工具都在問 **「這是真的嗎？」**。Claimproof 問的是另一個問題：
**「這項主張有可能失敗嗎？如果不可能，你就什麼都沒驗證到。」**

## 它做什麼

在回報完成之前，agent 必須輸出一張 **Claim Receipt（主張收據）**：

```
DONE       What I claim is now true. One sentence, falsifiable.
MEASURED   The actual number / output / bytes. Not what I set. What I observed.
INSTRUMENT What measured it, plus the positive control proving it can see.
NEGATIVE   The deliberately-broken sample I ran, and that it went red.
BLIND      What I did NOT measure. Not "nothing" — name the gap.
FALSIFIER  What evidence would overturn the DONE line above.
```

如果某個欄位填不出來，**那本身就是發現** —— 該主張標記為 `UNVERIFIED`，
而不是被當成成功回報。

## 安裝

```bash
# user level (available in every project)
cp -r claimproof ~/.dsh/skills/claimproof

# or project level
cp -r claimproof <your-project>/.dsh/skills/claimproof
```

DSH 會從檔案系統自動探索 skill —— 不需要重啟。

## 檢查器

```bash
python3 scripts/check_claim.py report.md   # 0 PASS / 1 BLOCK / 2 UNVERIFIED
python3 scripts/self_test.py               # the negative-sample protocol
```

**它能做什麼：** 拒絕空洞的收據。六個 `x` 字元、一個坦承「什麼都沒量」的
欄位、或一個薄到不構成觀察的 `MEASURED`，都會被擋下。

**它不能做什麼：** 證明一項主張為真。一份自信、詳細、但完全捏造的收據照樣
通過。這是防堵空洞回報的地板，不是正確性的證明。不要把 PASS 講得比它實際
更大。

檢查器本身也受它自己主張的規則約束。`self_test.py` 跑九個 fixture，其中四個是
**故意寫壞、必須失敗**的。

兩個真實的 bug 就是這樣被抓到的，都是靠故意寫壞的樣本：

- 欄位正規表示式用了 `\s`，把下一行吸收成自己的值，導致空白的 `MEASURED` 欄位
  回報 PASS；
- 第一版接受六個 `x` 字元當作完整收據 —— 這是對抗性審查發現的，它指出：
  一個任何人都無法讓它失敗的檢查器，正是這個 skill 自己在警告的那件事。

詳見 `evals/README.md`。

上面每一項檢查 —— 兩個自測與全部十組翻譯配對 —— 都會在每次 push 時透過 `scripts/verify.py` 在 CI 執行。見 `.github/workflows/verify.yml`。

## 強度等級

| 等級 | 行為 |
| --- | --- |
| `lite` | 在任何完成主張後面加一行 `FALSIFIER:`。便宜，能攔下過度自信。 |
| `full` *（預設）* | 每次完成主張都輸出完整收據；涉及檢查時要跑負樣本。 |
| `ultra` | 完整收據 **加上** 在宣稱之前先主動尋找反例 —— 先試著弄壞自己的成果，並回報弄壞了什麼。 |

## 翻譯

| 語言 | README | Skill 與參考文件 |
| --- | --- | --- |
| English *（正典）* | [README.md](README.md) | [SKILL.md](SKILL.md)、[references/](references/) |
| 繁體中文 | 本檔 | [i18n/zh-Hant/](i18n/zh-Hant/) |
| 简体中文 | [README.zh-Hans.md](README.zh-Hans.md) | [i18n/zh-Hans/](i18n/zh-Hans/) |

DSH 永遠載入根目錄的 `SKILL.md`。`i18n/` 底下的檔案深度不夠，不會被
探索成 skill，因此永遠不會造成觸發歧義。翻譯政策與「如何偵測漏譯」見
[i18n/README.md](i18n/README.md)。

翻譯的漏譯內容由 `scripts/check_translations.py` 檢查，它比對結構、數字與程式碼
區塊 —— 而它自己的自測證明了它會失敗。

## 專案結構

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

## 它有用嗎？

未知，而且只量到一部分。一項雙 agent 實驗發現：在一個小型分頁 bug 上，
**claimproof 沒有攔下任何錯誤** —— 對照組與實驗組都找到並修好了 bug。
實際量到的差異更窄：實驗組的報告寫出了它**沒有**驗證的部分，而且可被機械檢查。

同一個實驗也發現：檢查器會**拒絕一份完全正確的散文報告**，因為它評的是格式，不是真偽。
信任任一邊的結論之前，請先讀 [docs/comparison.md](docs/comparison.md)。

## 唯一的一條規則

> **不會失敗的檢查，等於沒有檢查。**

如果你從來沒看過某個檢查變紅，你就不會知道它到底有沒有在看。

## 授權

MIT
