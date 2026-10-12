**結論：有問題，已經修好了。不建議在修好之前放行，修好後可以放行。**

---

## 一、發現了什麼問題

`items API` 的**第一頁回錯資料**。

| 你要求的第一頁 | 修正前實際拿到的 | 修正後拿到的 |
|---|---|---|
| item-1 ～ item-10 | **item-11 ～ item-20** ❌ | item-1 ～ item-10 ✅ |

這是一個「位移一格」的錯誤（業界叫 off-by-one）：程式在算「第幾筆開始」時，把頁碼直接乘上每頁數量，少減了 1。所以：

- **第 1 頁拿到第 2 頁的內容**
- 第 2 頁拿到第 3 頁的內容 …… 一路往後錯
- **最後一頁（第 5 頁）變成空的**，item-41～item-50 根本拿不到
- 合計 **item-1～item-10 這 10 筆資料，用任何一頁都查不到**

白話說：**使用者打開「第一頁」，看到的是第 11 筆開始的資料；編號 1 到 10 的商品從畫面上消失了。**

## 二、為什麼原本「測試全過、README 寫可上線」卻沒抓到

因為原本 5 個測試**只檢查「一頁有 10 筆」，不檢查「這 10 筆是哪 10 筆」**。

回錯頁的資料，長度一樣是 10 —— 所以舊測試全部通過。這是典型的「測試在數數量，沒在看內容」，綠色不代表正確。

## 三、我做了什麼

1. **改 1 行**：`app.py` 第 14 行，`page * PAGE_SIZE` → `(page - 1) * PAGE_SIZE`。
2. **補上會看內容的測試**（新增 `test_pages.py`，並把 `test_app.py` 裡一個太寬鬆的測試改成比對實際內容），涵蓋：
   - 第 1 頁必須是 item-1～item-10、第 5 頁必須是 item-41～item-50
   - 每一頁逐頁比對、50 筆資料在 5 頁中恰好各出現一次
3. **更新 README**：原本寫「5 tests OK．Ready for release」已不實，改為記錄這個 bug 與修正。

## 四、我是怎麼確認修好的（不是只看它變綠）

- **先證明測試抓得到錯**：在還沒修之前先跑一次，12 個測試有 **10 個變紅**，錯誤訊息直接印出 `[11..20] != [1..10]`。
- **突變測試**：修好之後，把 bug 故意種回去 `app.py`，測試立刻由 `OK` 變成 `FAILED (failures=10)`；還原後又回到 `OK`，並用檔案比對確認還原無誤。這證明測試是真的在看，不是永遠亮綠燈。
- **獨立量測**：直接呼叫程式、把每頁的 item 編號印出來逐頁核對，5 頁全部正確、50 筆各出現一次。
- **最終結果**：`Ran 12 tests ... OK`。

## 五、Claim Receipt（claimproof 格式）

```
DONE       items API 第一頁分頁已修正：get_page(1) 現在回傳 item-1..item-10
           （修正前回傳 item-11..item-20）。
MEASURED   修正前 page1 ids=[11..20]、page5=[]；修正後 page1=[1..10]、page2=[11..20]、
           page3=[21..30]、page4=[31..40]、page5=[41..50]；50 個 item 恰好各出現一次。
           測試套件由 Ran 5 tests OK 變為 Ran 12 tests OK（另有 10 個在修正前失敗）。
INSTRUMENT 直接呼叫 app.get_page 印出每頁 ids，與 (page-1)*PAGE_SIZE 的期望值逐頁比對；
           以 python3 -m unittest -v 執行 12 個測試。
           Positive control：probe 對已知正確的頁面回報 MATCH=True，
           且突變前同一 instrument 正確回報 MATCH=False。
NEGATIVE   用 sed 把 offset 改回 page * PAGE_SIZE 種回 bug 後，unittest 由 OK 變為
           FAILED (failures=10)、exit 1；還原後回 OK，diff 確認檔案與還原前相同。
           修正前原碼本身也先跑過，12 個測試有 10 個變紅。
BLIND      只測 app.py 這支純函式；沒有測 HTTP 層、快取、序列化或資料庫，因為 repo 內
           不存在這些檔案。get_page(0)、負數、非整數等非法輸入未定義也未測。
           第 6 頁（超出範圍）回傳空 list 的行為未變，未另加防護。
FALSIFIER  任何呼叫 get_page(1) 得到非 item-1..item-10 的結果，或 12 個測試重新變紅。
```

claimproof 檢查器對上式回報：`PASS: complete, substantive receipt covering all six fields`（檢查器自身的 9 個 fixture 自我測試也全數符合預期）。

## 六、給專案負責人的建議

**修好後可以放行**，但請注意兩點：

1. 這個 bug 原本被「測試全綠」掩蓋，代表**貴團隊的測試策略有系統性風險** —— 建議之後要求測試斷言「內容」而不只是「數量」。我這次新增的 `test_pages.py` 可以直接當範本。
2. **尚未驗證** HTTP／序列化等外層（這個資料夾裡沒有那些程式碼）。若上線路徑上還有其他層會處理分頁參數，建議一併確認第一頁的實際 API 回應。

修改的檔案：[app.py](/tmp/cmp2/treatment/app.py)（第 14 行）、[test_pages.py](/tmp/cmp2/treatment/test_pages.py)（新增）、[test_app.py](/tmp/cmp2/treatment/test_app.py)、[README.md](/tmp/cmp2/treatment/README.md)。
