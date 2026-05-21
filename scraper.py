import json
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HKEX_SEARCH_URL = "https://www1.hkexnews.hk/search/titlesearch.xhtml"
FORM_DATA_TEMPLATE = {
    "lang": "EN",
    "category": "0",
    "market": "SEHK",
    "searchType": "0",
    "documentType": "-1",
    "t1code": "-2",
    "t2Gcode": "-2",
    "t2code": "-2",
    "stockId": "",  # set per request
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-HK;q=0.8,zh;q=0.7",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def load_config(config_path: str = "config.json") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def search_announcements(stock_id: str, lang: str = "en") -> list[dict]:
    """POST to HKEX search and return list of announcement dicts."""
    form_data = dict(FORM_DATA_TEMPLATE)
    form_data["stockId"] = stock_id
    form_data["lang"] = lang.upper()

    params = {"lang": lang.lower()}
    resp = SESSION.post(
        HKEX_SEARCH_URL, data=form_data, params=params, timeout=30
    )
    resp.raise_for_status()
    return parse_announcements(resp.text)


def parse_announcements(html: str) -> list[dict]:
    """Parse HKEX search result HTML into structured announcement data."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("table.sticky-header-table")
    if table is None:
        logger.warning("Could not find table.sticky-header-table in response")
        return []

    results = []
    for row in table.select("tbody tr"):
        release_time_el = row.select_one("td.release-time")
        headline_el = row.select_one(".headline")
        # .mobile-list-heading from the document cell (parent of .headline)
        doc_cell = headline_el.parent if headline_el else None
        heading_el = doc_cell.select_one(".mobile-list-heading") if doc_cell else None
        doc_link_el = row.select_one(".doc-link a")
        filesize_el = row.select_one(".attachment_filesize")

        release_time = ""
        if release_time_el:
            # Get text after the <span class="mobile-list-heading"> inside the td
            text_nodes = [
                t.strip() for t in release_time_el.find_all(string=True, recursive=False)
            ]
            release_time = text_nodes[-1] if text_nodes else release_time_el.get_text(strip=True)

        headline = headline_el.get_text(strip=True) if headline_el else ""
        category = heading_el.get_text(strip=True) if heading_el else ""

        # Skip rows without valid data (e.g. empty/separator rows)
        if not release_time and not headline:
            continue

        doc_url = doc_link_el.get("href", "") if doc_link_el else ""
        doc_filename = doc_link_el.get_text(strip=True) if doc_link_el else ""
        filesize = filesize_el.get_text(strip=True) if filesize_el else ""

        # Make doc_url absolute if relative
        if doc_url and doc_url.startswith("/"):
            doc_url = f"https://www1.hkexnews.hk{doc_url}"

        results.append(
            {
                "release_time": release_time,
                "headline": headline,
                "category": category,
                "doc_url": doc_url,
                "doc_filename": doc_filename,
                "filesize": filesize,
            }
        )

    return results


def fetch_all_announcements(config: dict) -> dict[str, list[dict]]:
    """Fetch announcements for all stocks in config. Returns {stock_code: [announcements]}."""
    all_results = {}
    for stock in config.get("stocks", []):
        code = stock["code"]
        stock_id = stock["stockId"]
        logger.info(f"Fetching announcements for {code} (stockId={stock_id})")
        try:
            announcements = search_announcements(stock_id)
            all_results[code] = announcements
            logger.info(f"  Got {len(announcements)} announcements for {code}")
        except Exception as e:
            logger.error(f"  Failed to fetch for {code}: {e}")
            all_results[code] = []
    return all_results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    config = load_config()
    results = fetch_all_announcements(config)
    for code, announcements in results.items():
        print(f"\n=== {code} ({len(announcements)} announcements) ===")
        for a in announcements[:5]:
            print(f"  {a['release_time']} | {a['headline']}")
            if a["doc_url"]:
                print(f"    PDF: {a['doc_url']}")
