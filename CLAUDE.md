# CLAUDE.md - HKEX Notifier

## Project Overview

HKEX Notifier 是一個 Python 應用程式，定時監控香港交易所披露易網站上指定股票的公告更新，發現新公告時透過 SMTP 發送 email 通知。

## Commands

```bash
# 初次設定
python -m venv venv
source venv/Scripts/activate   # Windows
source venv/bin/activate       # Linux
pip install -r requirements.txt

# 手動執行 scraper 測試
python scraper.py

# 啟動定時排程
python scheduler.py
```

## Architecture

```
config.json          →  設定檔（stockId 列表、SMTP、收件人、排程頻率）
scraper.py           →  POST + BeautifulSoup 解析 HKEX 公告列表
state.py             →  SQLite 操作（announcements / fetch_log / email_log）
notifier.py          →  SMTP email 發送（HTML 表格格式）
scheduler.py         →  APScheduler 定時執行完整 pipeline
hkex_notifier.db     →  SQLite 資料庫（運行時自動產生）
production/          →  systemd service 部署檔
```

### Pipeline: scraper → find new → record → notify → log email

## Key Technical Details

### HKEX Scraping
- POST to `https://www1.hkexnews.hk/search/titlesearch.xhtml?lang=en`
- Form data includes `stockId` (not stock code — provided directly by user)
- Results in `table.sticky-header-table`, each row = `tbody > tr`
- Fields: `td.release-time`, `.headline`, `.doc-link a`, `.attachment_filesize`

### SQLite Schema
- `announcements` — 所有已擷取公告，UNIQUE(stock_code, release_time, headline)
- `fetch_log` — 每次擷取的時間／結果數／成功狀態
- `email_log` — 每次 email 發送的時間／收件人／成功狀態

### Config
- `config.json` 是唯一設定來源（stocks、SMTP、recipients、check_interval_hours）
- `config.json` 不應 commit（含 SMTP 憑證）

### Production (Ubuntu)
- systemd service: `production/hkex-notifier.service`
- 部署路徑: `/home/goodwin/hkex_notifier/`
- User: `goodwin`
