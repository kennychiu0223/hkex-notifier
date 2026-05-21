# TODO - HKEX Notifier

## 1. 專案初始化 ✅
- [x] 建立 Python virtual environment
- [x] 建立 `requirements.txt`
- [x] 建立 `config.json` 設定檔模板

## 2. Scraper 模組 (`scraper.py`) ✅
- [x] 實作 POST 請求到 HKEX 搜尋頁面
- [x] 解析 `table.sticky-header-table` 公告列表
- [x] 提取 release-time / headline / doc-link / filesize
- [x] 支援多個 stockId 依序搜尋
- [x] 回傳結構化公告資料

## 3. 狀態管理 (`state.py`) ✅
- [x] SQLite 資料庫初始化（announcements / fetch_log / email_log）
- [x] record_fetch — 記錄每次擷取（含公告 insert or ignore）
- [x] find_new_announcements — 比對已存公告，找出新公告
- [x] log_email — 記錄每次 email 發送結果

## 4. Email 通知 (`notifier.py`) ✅
- [x] SMTP 連線 + HTML 表格 email
- [x] 支援多收件人 / 多筆公告合併發送
- [x] 實際發送測試通過

## 5. 排程 (`scheduler.py`) ✅
- [x] APScheduler 定時執行完整 pipeline
- [x] scrape → find new → record → notify → log email
- [x] Error handling（網路失敗不中斷排程）
- [x] 頻率改為 hours（預設每 1 小時）

## 6. 測試與驗證 ✅
- [x] Scraper 正確擷取 HKEX 公告
- [x] State 新舊比對邏輯測試
- [x] Email 實際發送測試
- [x] 端到端流程測試（首次 4 新 → email → 二次 0 新）

## 7. Production 部署
- [x] systemd service file (`production/hkex-notifier.service`)
- [ ] 部署至 Ubuntu server 並啟動
