import logging

from apscheduler.schedulers.blocking import BlockingScheduler

import scraper
import notifier
import state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("scheduler")


def check_and_notify():
    """Main pipeline: scrape → record → compare → notify → log email."""
    logger.info("Starting check cycle")
    state.init_db()

    config = scraper.load_config()
    all_announcements = scraper.fetch_all_announcements(config)

    for stock_code, announcements in all_announcements.items():
        if not announcements:
            state.record_fetch(stock_code, [], success=True)
            continue

        # Check which are new before recording (compare against existing DB)
        new_announcements = state.find_new_announcements(stock_code, announcements)

        # Record all fetched announcements into DB
        new_count = state.record_fetch(stock_code, announcements, success=True)
        logger.info(f"{stock_code}: {new_count} new announcements inserted into DB")

        if new_announcements:
            logger.info(
                f"{stock_code}: {len(new_announcements)} new announcement(s) found, sending email"
            )
            subject = f"[HKEX Notifier] {stock_code} - {len(new_announcements)} new announcement(s)"
            recipients = config.get("recipients", [])
            success = notifier.send_announcement_email(
                config, stock_code, new_announcements
            )
            state.log_email(
                stock_code=stock_code,
                num_announcements=len(new_announcements),
                recipients=recipients,
                subject=subject,
                success=success,
            )

    logger.info("Check cycle complete")


def main():
    state.init_db()
    config = scraper.load_config()
    interval = config.get("check_interval_hours", 1)

    scheduler = BlockingScheduler()
    scheduler.add_job(
        check_and_notify,
        "interval",
        hours=interval,
        id="check_announcements",
    )

    logger.info(f"Scheduler started, checking every {interval} hour(s)")
    check_and_notify()
    scheduler.start()


if __name__ == "__main__":
    main()
