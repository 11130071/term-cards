# 術語卡 Term Cards

**網站：<https://11130071.github.io/term-cards/>**

把課程與工作中遇到的**英文專業術語**整理成一張張卡片的小網站。每張卡有：

- 英文術語（縮寫會附上完整英文）
- 台灣常用的中文譯名
- 一句白話解釋
- 真實情境的英文例句與中文翻譯
- 補充說明與相關術語（選填）

## 可以拿來做什麼

- **查詢**：首頁的搜尋框可以跨主題找術語，英文、縮寫或中文都能搜。按 `/` 可以直接跳到搜尋框。
- **自我測驗**：在主題頁開啟「測驗模式」，卡片只會顯示英文術語，先自己回想中文意思，再點卡片翻開確認。可以打亂順序，畫面上會顯示翻開了幾張。
- **持續累積**：遇到新術語就加一張卡，遇到新領域就加一個主題，不需要改任何程式。

網站是純靜態的 HTML、CSS、JavaScript，沒有用任何框架或建置工具，部署在 GitHub Pages。支援深色模式，手機也能用。

## 本機預覽

網站用 `fetch()` 讀取 JSON 資料，**直接雙擊 HTML 檔會讀不到內容**，要先開本機伺服器。在專案資料夾執行：

```bash
# Windows
python -m http.server 8000

# macOS / Linux
python3 -m http.server 8000
```

再用瀏覽器開啟 <http://localhost:8000/>。

## 新增內容

所有術語都寫在 `topics/` 裡的 JSON 檔，一個主題一個檔案。**新增內容只需要改 JSON，不需要動 HTML、CSS 或 JavaScript。**

### 在既有主題加一張卡

1. 打開 `topics/<主題>.json`，在 `terms` 陣列中加入一張卡：

   ```json
   {
     "term": "DNS",
     "full": "Domain Name System",
     "zh": "網域名稱系統",
     "explain": "把網址轉換成 IP 位址的系統，就像網路的電話簿。",
     "example": "If DNS fails, you can't open websites by name.",
     "example_zh": "如果 DNS 故障，就沒辦法用網址開啟網站。",
     "note": "常見的公開 DNS：8.8.8.8、1.1.1.1。",
     "related": ["Gateway"]
   }
   ```

   `full`（只有縮寫才寫）、`note`、`related` 是選填。卡片依「先基礎、後進階」排列，不一定要加在最後。
2. 把該主題的 `updated` 改成今天的日期（`YYYY-MM-DD`）。
3. 執行檢查（見下一節）。

### 新增一個主題

1. 複製 `templates/topic-template.json`，改名為 `topics/<slug>.json`。slug 只能用小寫英文、數字與連字號，例如 `cloud-computing`。
2. 填好主題名稱、說明與日期，並寫入**至少 8 張卡**。
3. 在 `topics/index.json` 的**最後面**登記這個主題，並選一個顏色：

   ```json
   { "slug": "cloud-computing", "accent": "teal" }
   ```

   可用的顏色有 `blue`、`purple`、`amber`、`green`、`rose`、`teal`，不要和前一個主題同色。
4. 執行檢查，再用本機預覽確認首頁有出現新主題、主題頁顯示正常。

主題頁的網址是 `topic.html?t=<slug>`，不需要另外建立 HTML 檔。

## 檢查內容

每次修改完都要執行規則檢查：

```bash
# Windows
python tools/check.py

# macOS / Linux
python3 tools/check.py
```

這支程式會檢查必填欄位、字數上限、例句是否包含術語、`related` 是否指向存在的術語、簡體字與大陸用語、是否寫到公開 IP 或 Email 等。

- **錯誤（✗）**：違反規則，一定要修正，修好前不算完成。
- **警告（!）**：程式無法確定，例如「數據」是不是指 data，請人工判斷。

加上 `--strict` 的話，警告也會算成錯誤。

翻譯是否正確、例句是否自然，程式沒辦法判斷，需要自己再看一次。

## 檔案結構

```
term-cards/
├── index.html              首頁：列出所有主題
├── topic.html              主題頁：topic.html?t=<slug>
├── assets/                 樣式與程式（全站共用）
├── topics/                 術語內容：index.json 主題清單＋每個主題一個檔案
├── templates/              新增主題用的範本
├── tools/check.py          規則檢查程式
├── CLAUDE.md               完整的撰寫規則（也是給 Claude Code 看的專案規則）
└── .nojekyll               GitHub Pages 需要，請勿刪除
```

## 撰寫規則

完整規則寫在 [CLAUDE.md](CLAUDE.md)，最重要的幾條：

- 全部使用**台灣繁體中文與台灣用語**，例如網路、資料、軟體、伺服器。
- **只寫確定正確的內容**，不確定就不要寫，也不要編造數字或規格。
- **一張卡只解釋一個概念**，容易混淆的兩個詞各寫一張，用 `related` 互相連結。
- 網站是公開的，**不要寫入真實的伺服器位址、帳號密碼或個人資料**。例句中的 IP 只用私有位址（例如 `192.168.1.1`）。
