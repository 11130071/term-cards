# CLAUDE.md：英文術語卡（Term Cards）

這份文件是給 Claude Code 看的專案規則。新增或修改任何內容前，請先完整讀完本文件，並在完成後執行第 8 節的檢查。

## 1. 專案目的

把我在課程與工作中遇到的**英文專業術語**整理成「術語卡」網站，用來：

- 查詢：忘記某個術語的意思時，快速找到中文、解釋與例句。
- 自我測驗：開啟「測驗模式」，只看英文，自己回想中文再翻卡確認。
- 持續累積：每遇到新術語就加一張卡，每遇到新領域就加一個主題。

我是**以繁體中文為母語、正在學習專業英文的學生**。所有中文都要用台灣用語。

## 2. 技術限制

- 純靜態網站：HTML + CSS + 原生 JavaScript，**不使用任何框架、套件或建置工具**，也不要加入 `package.json`。
- 部署在 GitHub Pages，根目錄有 `.nojekyll`，不要刪除。
- 唯一允許的外部資源是 Google Fonts（`Noto Sans TC`、`IBM Plex Mono`）。
- **內容與畫面分離**：術語內容只寫在 `topics/*.json`，`index.html`、`topic.html`、`assets/` 不放任何術語內容。新增術語或主題時，**不需要也不應該修改 HTML、CSS、JS**。

## 3. 檔案結構

```
term-cards/
├── CLAUDE.md               ← 本文件：專案規則
├── README.md               ← 給我看的專案介紹
├── index.html              ← 首頁：列出所有主題（讀取 topics/index.json）
├── topic.html              ← 主題頁：topic.html?t=<slug> 顯示該主題的術語卡
├── assets/
│   ├── style.css           ← 全站唯一樣式表
│   └── app.js              ← 全站唯一程式（首頁與主題頁共用）
├── topics/
│   ├── index.json          ← 主題清單（決定首頁顯示哪些主題、順序）
│   ├── network.json        ← 一個主題一個檔案
│   ├── ai.json
│   └── measurement.json
├── templates/
│   └── topic-template.json ← 新增主題時複製這個檔案
└── tools/
    └── check.py            ← 規則檢查程式
```

## 4. 命名與放置規則

| 項目 | 規則 | 範例 |
|---|---|---|
| 主題檔名 | `topics/<slug>.json`，slug 為小寫英文、數字與連字號 | `topics/network.json`、`topics/cloud-computing.json` |
| slug | 必須與檔名相同，且與 `topics/index.json` 中的 `slug` 相同 | `"slug": "network"` |
| 網址 | 主題頁一律用 `topic.html?t=<slug>`，不要為主題另外建立 HTML 檔 | `topic.html?t=ai` |
| 主題順序 | 由 `topics/index.json` 陣列順序決定，新主題加在最後 | — |

## 5. 資料格式

### 5-1. 主題清單 `topics/index.json`

```json
[
  { "slug": "network", "accent": "blue" }
]
```

- `accent`：主題顏色，**只能**從 `blue`、`purple`、`amber`、`green`、`rose`、`teal` 中選一個。不可新增顏色或寫色碼，顏色定義在 `assets/style.css`。
- 相鄰兩個主題不要用同一個顏色。

### 5-2. 主題檔 `topics/<slug>.json`

```json
{
  "slug": "network",
  "title_zh": "網路",
  "title_en": "Networking",
  "description": "網管工作與網路課程常見的術語。",
  "updated": "2026-11-16",
  "terms": [
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
  ]
}
```

| 欄位 | 必填 | 規則 |
|---|---|---|
| `term` | ✅ | 英文術語。縮寫寫縮寫本身（`DNS`），一般名詞首字大寫（`Bandwidth`）。同一主題內不可重複（不分大小寫） |
| `full` | 縮寫時必填 | 縮寫的完整英文。不是縮寫就不要寫這個欄位 |
| `zh` | ✅ | 台灣常用的中文譯名，有兩種常見說法時用「、」分隔，最多兩個 |
| `explain` | ✅ | 一句白話解釋，**40 字以內**，不要只重複中文譯名 |
| `example` | ✅ | 英文例句，**必須包含 `term` 本身**（不分大小寫，可以是複數形），**25 個英文字以內**，要是該領域真的會出現的句子 |
| `example_zh` | ✅ | 例句的台灣繁體中文翻譯，意思要與英文一致 |
| `note` | 選填 | 補充：易混淆的詞、常見用法、單位、注意事項，**60 字以內** |
| `related` | 選填 | 同一主題內相關術語的 `term`，必須是這個主題中**已經存在**的術語 |
| `updated` | ✅（主題） | 最後修改日期，格式 `YYYY-MM-DD`，每次修改該主題都要更新 |

## 6. 內容撰寫規則

1. **台灣繁體中文**：不可出現簡體字；使用台灣用語，例如「網路」不是「網絡」、「資料」不是「數據」（指 data 時）、「軟體」不是「軟件」、「品質」不是「質量」、「程式」不是「程序」、「伺服器」不是「服務器」、「三用電錶」不是「萬用表」。
2. **正確性優先**：只寫確定正確的內容。不確定的定義寧可不寫，不要編造數據、標準或規格數字。例句不要寫依賴實際量測或特定地點的具體數字（例如「連到東京伺服器的延遲大約 40 ms」）。
3. **一卡一概念**：一張卡只解釋一個術語。兩個詞容易混淆時，各寫一張卡，並在 `note` 說明差別、在 `related` 互相連結。
4. **例句要像真的**：例句情境要符合該領域的實際使用場景（工作對話、說明書、技術文件），不要寫「This is a DNS.」這種沒有資訊量的句子。
5. **不放敏感資訊**：網站公開在 GitHub，不可寫入真實的伺服器位址、帳號密碼、內部系統路徑或個人資料。例句中的 IP 只用私有位址（`192.168.x.x`、`10.x.x.x`、`172.16.x.x`、`172.31.x.x`）或公開 DNS 這類通用例子。
6. **每個主題至少 8 張卡**，主題內的術語依「先基礎、後進階」排列。

## 7. 常見工作流程

### 新增術語到既有主題

1. 打開 `topics/<slug>.json`，在 `terms` 陣列加入一個物件，欄位依第 5-2 節。
2. 依難度放在適當位置（不一定加在最後）。
3. 更新該主題的 `updated` 日期。
4. 執行 `python tools/check.py`，全部通過才算完成。

### 新增一個主題

1. 複製 `templates/topic-template.json` 為 `topics/<新 slug>.json`。
2. 填入 `slug`、`title_zh`、`title_en`、`description`、`updated`，並寫入至少 8 張卡。
3. 在 `topics/index.json` 最後加入 `{ "slug": "<新 slug>", "accent": "<顏色>" }`，顏色不可與前一個主題相同。
4. 執行 `python tools/check.py`。
5. 本機預覽確認首頁出現新主題、主題頁正常顯示（見第 9 節）。

### 修改畫面或功能

只有在我**明確要求修改外觀或功能**時，才可以修改 `index.html`、`topic.html`、`assets/`。修改時：

- 顏色一律使用 `style.css` 中的 CSS 變數，不要在 HTML 或 JS 中寫死色碼。
- 必須同時支援淺色與深色模式（`prefers-color-scheme`）、手機寬度（360px）不出現水平捲軸。
- 修改後確認三個既有主題頁都還能正常顯示。

## 8. 完成前的檢查（必做）

```bash
python tools/check.py
```

這支程式會檢查第 4～6 節中可以自動判斷的規則：必填欄位、slug 與檔名一致、主題有登記在 `index.json`、顏色在允許清單內、術語不重複、例句包含術語、字數上限、`related` 指向存在的術語、常見簡體字與大陸用語。**有任何錯誤就不算完成**，請修正後再執行一次。

程式無法判斷的部分（翻譯是否正確、例句是否自然、內容是否正確），由 AI 自行檢查，並在回報時說明。

## 9. 本機預覽

網站用 `fetch()` 讀取 JSON，直接雙擊 HTML 檔會讀不到資料，要開本機伺服器：

```bash
python -m http.server 8000
```

再開啟 `http://localhost:8000/`。

這個專案在 Windows 上開發，Windows 請用 `python`；macOS / Linux 才用 `python3`（本文件中的 `python` 指令都依此替換）。

## 10. 禁止事項

- 不要在 HTML 中直接寫術語內容，也不要為單一主題建立獨立的 HTML 檔。
- 不要引入任何 JavaScript 框架、CSS 框架、CDN 套件或建置工具。
- 不要刪除或改名既有的主題 slug（會讓別人收藏的網址失效）；要改名時先詢問我。
- 不要一次大量改寫我已經寫好的卡片內容；只修改被要求的部分，發現既有內容有錯誤時先回報。

## 11. Commit 訊息格式

```
<類型>: <說明>
```

類型為 `term`（新增或修改術語）、`topic`（新增主題）、`ui`（畫面或功能）、`docs`（文件）。例如：`term: 新增 network 主題 3 張卡（VLAN、MTU、NAT）`。
