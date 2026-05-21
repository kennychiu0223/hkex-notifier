# HKEX Notifier

香港交易所披露易公告監控通知系統。定時搜尋指定股票的公告更新，發現新公告時以 email 通知。

## Quick Start

```bash
# 安裝
python -m venv venv
source venv/bin/activate      # Linux
# source venv/Scripts/activate # Windows
pip install -r requirements.txt

# 設定 config.json（stockId、SMTP、收件人）

# 執行
python scheduler.py
```

## 運作流程

```
POST HKEX → 解析公告列表 → SQLite 比對新舊 → 新公告 → SMTP email 通知
                                               ↓
                                        record fetch + log email
```

每次擷取和 email 發送均記錄至 `hkex_notifier.db`。

## 設定檔

`config.json`:
- `stocks` — 股票清單（code + stockId）
- `smtp` — SMTP 伺服器設定
- `recipients` — 通知收件人
- `check_interval_hours` — 檢查頻率（小時）

## 手動測試

```bash
python scraper.py    # 測試擷取
python scheduler.py  # 完整執行（會立即跑一次）
```

## Production 部署 (Ubuntu + systemd)

```bash
sudo cp production/hkex-notifier.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now hkex-notifier
```

查看狀態：
```bash
sudo systemctl status hkex-notifier
journalctl -u hkex-notifier -f
```

## 資料庫

| 資料表 | 內容 |
|--------|------|
| `announcements` | 已擷取公告（不重複） |
| `fetch_log` | 每次擷取記錄 |
| `email_log` | 每次 email 發送記錄 |

## Tech

Python `requests` + `BeautifulSoup4` + `APScheduler` + SQLite
