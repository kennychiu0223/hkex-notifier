import json
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.json") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def send_announcement_email(
    config: dict,
    stock_code: str,
    announcements: list[dict],
) -> bool:
    """Send email notification for new announcements of a stock."""
    smtp_config = config.get("smtp", {})
    recipients = config.get("recipients", [])

    if not recipients:
        logger.warning("No recipients configured, skipping email")
        return False

    if not announcements:
        return False

    subject = f"[HKEX Notifier] {stock_code} - {len(announcements)} new announcement(s)"

    # Build HTML body
    rows_html = ""
    for a in announcements:
        doc_link = f'<a href="{a["doc_url"]}">{a["doc_filename"] or a["doc_url"]}</a>'
        rows_html += f"""
        <tr>
            <td style="padding:8px;border:1px solid #ddd;">{a['release_time']}</td>
            <td style="padding:8px;border:1px solid #ddd;">{a['category']}</td>
            <td style="padding:8px;border:1px solid #ddd;">{a['headline']}</td>
            <td style="padding:8px;border:1px solid #ddd;">{doc_link}</td>
            <td style="padding:8px;border:1px solid #ddd;">{a['filesize']}</td>
        </tr>"""

    html_body = f"""
    <html><body>
    <h2>HKEX Notifier - {stock_code} New Announcements</h2>
    <p>{len(announcements)} new announcement(s) found.</p>
    <table style="border-collapse:collapse;width:100%;">
        <tr style="background:#f5f5f5;">
            <th style="padding:8px;border:1px solid #ddd;text-align:left;">Release Time</th>
            <th style="padding:8px;border:1px solid #ddd;text-align:left;">Category</th>
            <th style="padding:8px;border:1px solid #ddd;text-align:left;">Headline</th>
            <th style="padding:8px;border:1px solid #ddd;text-align:left;">PDF</th>
            <th style="padding:8px;border:1px solid #ddd;text-align:left;">Size</th>
        </tr>
        {rows_html}
    </table>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_config.get("from", "")
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(smtp_config["host"], smtp_config["port"], timeout=15) as server:
            server.starttls()
            server.login(smtp_config["username"], smtp_config["password"])
            server.sendmail(smtp_config["from"], recipients, msg.as_string())
        logger.info(f"Email sent to {recipients} for {stock_code}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email for {stock_code}: {e}")
        return False
