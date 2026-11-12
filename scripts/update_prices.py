"""Fetch today's mandi prices from data.gov.in and save them to the database.

data.gov.in refuses connections from outside India, so the deployed backend
(MARKET_PRICES_FROM_DB=true) can't fetch prices itself. Run this on a PC in India,
pointed at the same database, and the backend serves what it saves.

Settings come from .env, with .env.prices on top. Put the cloud database details
in .env.prices so your normal .env can keep pointing at your local MySQL:

    MYSQL_HOST=...
    MYSQL_PORT=4000
    MYSQL_USER=...
    MYSQL_PASSWORD=...
    MYSQL_DATABASE=agrimind
    MYSQL_SSL=true

Run it by hand:    venv\\Scripts\\python.exe scripts\\update_prices.py
Or on a schedule:  see "Mandi prices on the deployed backend" in the README.
Output goes to the console and to scripts/update_prices.log.
"""
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)   # .env, .env.prices and the model cache are relative to the project
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

if (ROOT / ".env.prices").exists():
    load_dotenv(ROOT / ".env.prices", override=True)   # environment beats .env in config.py
os.environ["MARKET_PRICES_FROM_DB"] = "false"          # this script is the one that fetches

handlers = [logging.FileHandler(ROOT / "scripts" / "update_prices.log", encoding="utf-8")]
if sys.stdout:   # pythonw (used by Task Scheduler) has no console
    handlers.append(logging.StreamHandler(sys.stdout))
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=handlers)
log = logging.getLogger("update_prices")


def main() -> int:
    from config import settings
    from database import init_db
    from agents import market_agent as ma

    if not settings.DATA_GOV_API_KEY:
        log.error("DATA_GOV_API_KEY is not set in .env")
        return 1
    log.info("Fetching mandi prices, saving to %s:%s/%s", settings.MYSQL_HOST, settings.MYSQL_PORT, settings.MYSQL_DATABASE)
    try:
        init_db()   # creates the tables if this is a new database
        records = ma._fetch_all_records()
        prices = ma._build_live_prices(records)
    except Exception as e:
        log.error("Failed: %s: %s", type(e).__name__, ma._redact(e))
        return 1

    log.info("Saved %d/%d crops from %d records", len(prices), len(ma.TRACKED_CROPS), len(records))
    for p in prices:
        change = f"{p['change']:+.1f}% since {p['prev_date']}" if p.get("prev_date") else "first day at this mandi"
        log.info("  %-10s Rs %6d  %s (%s)  %s", p["name"], p["price"], p["market"], p["date"], change)
    return 0 if prices else 1


if __name__ == "__main__":
    sys.exit(main())
