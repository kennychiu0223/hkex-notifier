# HKEX Notifier - 香港交易所披露易公告通知系統

## 功能需求

定時監控香港交易所披露易網站上指定股票的公告更新，當有新公告時發送 email 通知。

### 核心流程
1. 向 HKEX 披露易網站發送 POST 請求，搜尋指定股票代碼的公告
2. 解析搜尋結果頁面，提取公告列表（按發放時間排序）
3. 與 SQLite 中已記錄的公告比對，偵測新公告
4. 發現新公告時，發送 email 通知給指定收件人
5. 記錄每次擷取和 email 發送歷史

---

## Tech Stack

| 項目 | 選擇 |
|------|------|
| 語言 | Python 3.12+ |
| HTTP | `requests` |
| HTML 解析 | `BeautifulSoup4` |
| 排程 | `APScheduler` (in-process) |
| 狀態儲存 | SQLite (`hkex_notifier.db`) |
| 設定檔 | JSON (`config.json`) |
| Email | SMTP |
| 部署 | systemd (Ubuntu) |

---

## 專案結構

```
hkex-notifier/
├── config.json              # stockId 列表、SMTP、收件人、排程頻率
├── hkex_notifier.db         # SQLite（運行時產生）
├── scraper.py               # HTTP POST + HTML 解析
├── state.py                 # SQLite：announcements / fetch_log / email_log
├── notifier.py              # SMTP email 發送
├── scheduler.py             # APScheduler 排程入口
├── requirements.txt         # Python 相依套件
├── plan.md                  # 技術規格
├── todo.md                  # 工作清單
├── CLAUDE.md                # Claude 專案指引
├── README.md                # 專案說明
└── production/
    └── hkex-notifier.service  # systemd service
```

---

## 技術規格

### HTTP 請求
- **Method**: POST
- **URL**: `https://www1.hkexnews.hk/search/titlesearch.xhtml?lang=en`
- **Form Data**:
  ```
  lang=EN, category=0, market=SEHK, searchType=0, documentType=-1,
  t1code=-2, t2Gcode=-2, t2code=-2, stockId=<由使用者提供>
  ```

### HTML 解析 (CSS Selectors)
| 欄位 | Selector | 說明 |
|------|----------|------|
| 公告表格 | `table.sticky-header-table` | 搜尋結果表格 |
| 每筆公告 | `tbody > tr` | 一筆公告一個 row |
| 發放時間 | `td.release-time` | 文字節點（排除內部 span） |
| 標題 | `.headline` | 公告標題 |
| 文件類別 | `.mobile-list-heading` | document cell 內標籤 |
| PDF 連結 | `.doc-link a` | href + 文字 |
| 檔案大小 | `.attachment_filesize` | 附件大小 |

### SQLite Schema
**announcements** — 已擷取公告（UNIQUE: stock_code, release_time, headline）
**fetch_log** — 每次擷取記錄（時間、結果數、成功/失敗）
**email_log** — 每次發送記錄（時間、收件人、標題、成功/失敗）

### Email 通知
- SMTP 發送，HTML 表格格式
- 內容：股票代碼、公告標題、發放時間、PDF 連結、檔案大小
- 多筆公告合併為一封

### 定時排程
- APScheduler interval trigger
- 頻率：`config.json` 中 `check_interval_hours` 設定（預設 1 小時）

---

## config.json 結構

```json
{
  "stocks": [
    { "code": "08245", "stockId": "131915" }
  ],
  "smtp": {
    "host": "smtp.gmail.com",
    "port": 587,
    "username": "",
    "password": "",
    "from": ""
  },
  "recipients": ["notify@example.com"],
  "check_interval_hours": 1
}
```

## Production 部署 (Ubuntu)

1. 複製專案至 `/home/goodwin/hkex_notifier/`
2. 建立 venv: `python -m venv venv && pip install -r requirements.txt`
3. 設定 `config.json`
4. 安裝 service:
```bash
sudo cp production/hkex-notifier.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hkex-notifier
sudo systemctl start hkex-notifier
```
