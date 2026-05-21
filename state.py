import logging
import sqlite3
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

DB_FILE = "hkex_notifier.db"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                release_time TEXT NOT NULL,
                headline TEXT NOT NULL,
                category TEXT,
                doc_url TEXT,
                doc_filename TEXT,
                filesize TEXT,
                first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stock_code, release_time, headline)
            );

            CREATE TABLE IF NOT EXISTS fetch_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                num_results INTEGER,
                success BOOLEAN DEFAULT 1,
                error_message TEXT
            );

            CREATE TABLE IF NOT EXISTS email_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                num_announcements INTEGER,
                recipients TEXT,
                subject TEXT,
                success BOOLEAN DEFAULT 1,
                error_message TEXT
            );
        """)


def record_fetch(stock_code: str, announcements: list[dict], success: bool = True, error: str = "") -> int:
    """Record a fetch attempt and insert any new announcements. Returns number of new announcements inserted."""
    with get_db() as db:
        db.execute(
            "INSERT INTO fetch_log (stock_code, num_results, success, error_message) VALUES (?, ?, ?, ?)",
            (stock_code, len(announcements) if success else 0, int(success), error),
        )

        before = db.execute("SELECT COUNT(*) FROM announcements WHERE stock_code = ?", (stock_code,)).fetchone()[0]

        for a in announcements:
            db.execute(
                """INSERT OR IGNORE INTO announcements
                   (stock_code, release_time, headline, category, doc_url, doc_filename, filesize)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    stock_code,
                    a["release_time"],
                    a["headline"],
                    a.get("category", ""),
                    a.get("doc_url", ""),
                    a.get("doc_filename", ""),
                    a.get("filesize", ""),
                ),
            )

        after = db.execute("SELECT COUNT(*) FROM announcements WHERE stock_code = ?", (stock_code,)).fetchone()[0]
        return after - before


def find_new_announcements(stock_code: str, announcements: list[dict]) -> list[dict]:
    """Check which fetched announcements are not yet in the DB."""
    if not announcements:
        return []

    with get_db() as db:
        new_items = []
        for a in announcements:
            row = db.execute(
                """SELECT id FROM announcements
                   WHERE stock_code = ? AND release_time = ? AND headline = ?""",
                (stock_code, a["release_time"], a["headline"]),
            ).fetchone()
            if not row:
                new_items.append(a)
        return new_items


def log_email(
    stock_code: str,
    num_announcements: int,
    recipients: list[str],
    subject: str,
    success: bool = True,
    error: str = "",
) -> None:
    """Record an email send attempt."""
    with get_db() as db:
        db.execute(
            "INSERT INTO email_log (stock_code, num_announcements, recipients, subject, success, error_message) VALUES (?, ?, ?, ?, ?, ?)",
            (stock_code, num_announcements, ", ".join(recipients), subject, int(success), error),
        )


def get_recent_fetches(stock_code: str = "", limit: int = 20) -> list[dict]:
    """Query recent fetch logs, optionally filtered by stock."""
    with get_db() as db:
        if stock_code:
            rows = db.execute(
                "SELECT * FROM fetch_log WHERE stock_code = ? ORDER BY fetched_at DESC LIMIT ?",
                (stock_code, limit),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM fetch_log ORDER BY fetched_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]


def get_recent_emails(stock_code: str = "", limit: int = 20) -> list[dict]:
    """Query recent email logs, optionally filtered by stock."""
    with get_db() as db:
        if stock_code:
            rows = db.execute(
                "SELECT * FROM email_log WHERE stock_code = ? ORDER BY sent_at DESC LIMIT ?",
                (stock_code, limit),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM email_log ORDER BY sent_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
