import logging
import re
import threading
import time
from datetime import date, datetime

import requests
from sqlalchemy import func

from config import settings
from database import SessionLocal
from models import MarketPrice
from services.gemini_service import generate_json, GeminiUnavailableError
from rag.vector_store import similarity_search

logger = logging.getLogger(__name__)

MARKET_SYSTEM = """You are AgriMind's agricultural market analyst specializing in Indian commodity markets and APMC mandis.
Respond ONLY in valid JSON."""

# Agmarknet daily mandi prices, published on data.gov.in. Prices are in ₹/quintal.
DATA_GOV_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
# data.gov.in's firewall answers requests with Python's default User-Agent with a
# 502 after 60 seconds, so identify the app explicitly.
DATA_GOV_HEADERS = {"User-Agent": "AgriMind/1.0", "Accept": "application/json"}
PAGE_SIZE = 2000
MAX_PAGES = 25
REFRESH_SECONDS = 6 * 60 * 60   # the data only changes once a day
RETRY_SECONDS = 30 * 60         # after a failed refresh

# Tracked crops. Only crops with a live price are returned. MSP and category come
# from here because the feed doesn't include them. "market" is the preferred mandi,
# and "variety" is used when the feed gives none.
TRACKED_CROPS = [
    {"name": "Wheat", "variety": "HD-2967", "msp": 2275, "market": "Pune APMC", "state": "Maharashtra", "category": "Cereals"},
    {"name": "Rice", "variety": "Basmati 1121", "msp": 2300, "market": "Delhi Mandi", "state": "Delhi", "category": "Cereals"},
    {"name": "Soybean", "variety": "JS 9560", "msp": 4600, "market": "Indore APMC", "state": "Madhya Pradesh", "category": "Oilseeds"},
    {"name": "Cotton", "variety": "Bt Cotton", "msp": 7020, "market": "Nagpur Mandi", "state": "Maharashtra", "category": "Fibre"},
    {"name": "Sugarcane", "variety": "Co-86032", "msp": 315, "market": "Kolhapur", "state": "Maharashtra", "category": "Cash Crops"},
    {"name": "Onion", "variety": "Nasik Red", "msp": None, "market": "Lasalgaon", "state": "Maharashtra", "category": "Vegetables"},
    {"name": "Tomato", "variety": "Hybrid", "msp": None, "market": "Nashik", "state": "Maharashtra", "category": "Vegetables"},
    {"name": "Maize", "variety": "Hybrid-10", "msp": 2090, "market": "Nizamabad", "state": "Telangana", "category": "Cereals"},
    {"name": "Mustard", "variety": "Pusa Bold", "msp": 5650, "market": "Alwar Mandi", "state": "Rajasthan", "category": "Oilseeds"},
    {"name": "Chana", "variety": "Desi", "msp": 5440, "market": "Gulbarga", "state": "Karnataka", "category": "Pulses"},
]

# Agmarknet commodity names for each tracked crop, matched case-insensitively.
AGMARKNET_NAMES = {
    "Wheat": ["wheat"],
    "Rice": ["rice"],
    "Soybean": ["soyabean", "soybean"],
    "Cotton": ["cotton"],
    "Sugarcane": ["sugarcane"],
    "Onion": ["onion"],
    "Tomato": ["tomato"],
    "Maize": ["maize"],
    "Mustard": ["mustard"],
    "Chana": ["bengal gram(gram)(whole)", "bengal gram", "gram"],
}

_lock = threading.Lock()
_state = {"prices": None, "next_refresh": 0.0, "refreshing": False}


def _to_float(value):
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _to_date(value):
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            pass
    return None


def _with_change(p: dict) -> dict:
    """Add change %, trend and MSP difference."""
    prev = p.get("prev")
    change = round((p["price"] - prev) / prev * 100, 1) if prev else 0.0
    trend = "up" if change > 0 else "down" if change < 0 else "flat"
    msp_diff = round((p["price"] - p["msp"]) / p["msp"] * 100, 1) if p["msp"] else None
    return {**p, "change": change, "trend": trend, "msp_diff": msp_diff}


def _fetch_all_records() -> list[dict]:
    """Download the whole day's records. Filtering happens locally."""
    records, offset = [], 0
    for _ in range(MAX_PAGES):
        r = requests.get(
            DATA_GOV_URL,
            params={"api-key": settings.DATA_GOV_API_KEY, "format": "json",
                    "limit": PAGE_SIZE, "offset": offset},
            headers=DATA_GOV_HEADERS,
            timeout=(15, 90),
        )
        # Don't use raise_for_status(): its message contains the URL with the API key.
        if r.status_code != 200:
            raise RuntimeError(f"data.gov.in returned HTTP {r.status_code}")
        batch = r.json().get("records") or []
        records += batch
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return records


def _pick_record(seed: dict, records: list[dict], known_markets: list[str] = None):
    """Latest price for a crop, from the first of these that reported:
    1. a mandi with stored history, most recently used first, so the change %
       compares the same market (if the last mandi skips a day, an older one
       keeps the history going instead of starting over somewhere new)
    2. the preferred mandi
    3. the median mandi in the crop's home state (some states report far more mandis)
    4. the median mandi nationally"""
    names = AGMARKNET_NAMES[seed["name"]]
    rows = []
    for rec in records:
        if str(rec.get("commodity", "")).strip().lower() not in names:
            continue
        price, day = _to_float(rec.get("modal_price")), _to_date(rec.get("arrival_date"))
        if price and day:
            rows.append((day, price, rec))
    if not rows:
        return None

    latest = max(day for day, _, _ in rows)
    rows = sorted((r for r in rows if r[0] == latest), key=lambda r: r[1])
    by_market = {str(r[2].get("market", "")).strip().lower(): r for r in rows}
    for market in known_markets or []:
        row = by_market.get(market.strip().lower())
        if row:
            return row
    preferred = seed["market"].split()[0].lower()
    for row in rows:
        if preferred in str(row[2].get("market", "")).lower():
            return row
    home = [r for r in rows if str(r[2].get("state", "")).strip().lower() == seed["state"].lower()]
    rows = home or rows
    return rows[len(rows) // 2]


def _known_markets(db, crop: str, before: date) -> list[str]:
    """Every mandi stored for this crop before `before`, most recently used first.
    Today's rows don't count: an earlier run today may have used a stand-in mandi
    because the usual one hadn't reported yet (prices arrive through the day)."""
    before_start = datetime.combine(before, datetime.min.time())
    rows = db.query(MarketPrice.market, func.max(MarketPrice.recorded_at)) \
        .filter(MarketPrice.crop_name == crop, MarketPrice.recorded_at < before_start) \
        .group_by(MarketPrice.market) \
        .order_by(func.max(MarketPrice.recorded_at).desc(), func.max(MarketPrice.id).desc()).all()
    return [market for market, _ in rows if market]


def _prev_price_and_save(db, row: dict, day: date):
    """Return the last stored (price, date) for this crop and mandi, and store today's."""
    day_start = datetime.combine(day, datetime.min.time())
    same = db.query(MarketPrice).filter(
        MarketPrice.crop_name == row["name"], MarketPrice.market == row["market"]
    )
    prev = same.filter(MarketPrice.recorded_at < day_start).order_by(MarketPrice.recorded_at.desc()).first()
    today = same.filter(MarketPrice.recorded_at == day_start).first()
    if today:   # prices arrive through the day: keep the newest
        today.price, today.variety, today.state = row["price"], row["variety"], row["state"]
    else:
        db.add(MarketPrice(
            crop_name=row["name"], variety=row["variety"], price=row["price"],
            prev_price=prev.price if prev else None, msp=row["msp"], market=row["market"],
            state=row["state"], category=row["category"], recorded_at=day_start,
        ))
    return (prev.price, prev.recorded_at.date()) if prev else (None, None)


def _build_live_prices(records: list[dict]) -> list[dict]:
    prices = []
    days = [d for d in (_to_date(r.get("arrival_date")) for r in records) if d]
    latest_day = max(days) if days else date.today()
    db = SessionLocal()
    try:
        for seed in TRACKED_CROPS:
            picked = _pick_record(seed, records, _known_markets(db, seed["name"], latest_day))
            if not picked:
                logger.warning("No live mandi price for %s today; leaving it out", seed["name"])
                continue
            day, price, rec = picked
            row = {
                **seed,
                "variety": str(rec.get("variety") or "").strip() or seed["variety"],
                "price": round(price),
                "market": str(rec.get("market") or "").strip() or seed["market"],
                "state": str(rec.get("state") or "").strip() or seed["state"],
                "date": day.isoformat(),
            }
            prev, prev_day = _prev_price_and_save(db, row, day)
            # The change % compares with the last stored day at this mandi, which
            # is not always yesterday (mandis skip days).
            row["prev"] = prev
            row["prev_date"] = prev_day.isoformat() if prev_day else None
            prices.append(_with_change(row))
        db.commit()
    finally:
        db.close()
    return prices


def _redact(error: Exception) -> str:
    """The error message with the API key removed (request errors include the URL)."""
    message = str(error)
    if settings.DATA_GOV_API_KEY:
        message = message.replace(settings.DATA_GOV_API_KEY, "***")
    return re.sub(r"api-key=[^&\s'\"]+", "api-key=***", message)[:300]


def _refresh():
    try:
        prices = _build_live_prices(_fetch_all_records())
        print(f"📈 Mandi prices refreshed: {len(prices)}/{len(TRACKED_CROPS)} crops have live prices")
        with _lock:
            if prices:   # an empty answer keeps the last good prices
                _state["prices"] = prices
            _state["next_refresh"] = time.time() + (REFRESH_SECONDS if prices else RETRY_SECONDS)
    except Exception as e:
        logger.warning("Mandi price refresh failed (%s: %s); retrying in 30 minutes",
                       type(e).__name__, _redact(e))
        with _lock:
            _state["next_refresh"] = time.time() + RETRY_SECONDS
    finally:
        with _lock:
            _state["refreshing"] = False


def start_price_refresh():
    """Refresh prices in the background if they are due. Never blocks."""
    if settings.MARKET_PRICES_FROM_DB or not settings.DATA_GOV_API_KEY:
        return
    with _lock:
        if _state["refreshing"] or time.time() < _state["next_refresh"]:
            return
        _state["refreshing"] = True
    threading.Thread(target=_refresh, daemon=True).start()


SCHEDULER_CHECK_SECONDS = 15 * 60
_scheduler_started = False


def start_price_scheduler():
    """Keep prices refreshing while the server runs, even if nobody opens the
    Market tab, so each day's price gets stored."""
    global _scheduler_started
    if _scheduler_started or settings.MARKET_PRICES_FROM_DB or not settings.DATA_GOV_API_KEY:
        return
    _scheduler_started = True

    def loop():
        while True:
            start_price_refresh()   # does nothing until a refresh is due
            time.sleep(SCHEDULER_CHECK_SECONDS)

    threading.Thread(target=loop, daemon=True).start()


DB_CACHE_SECONDS = 10 * 60
_db_cache = {"prices": None, "at": 0.0}


def _prices_from_db() -> list[dict]:
    """Latest saved price per crop, in the same shape as live prices."""
    db = SessionLocal()
    try:
        prices = []
        for seed in TRACKED_CROPS:
            crop = db.query(MarketPrice).filter(MarketPrice.crop_name == seed["name"])
            # Newest id breaks ties: a later run today may have switched mandi.
            latest = crop.order_by(MarketPrice.recorded_at.desc(), MarketPrice.id.desc()).first()
            if not latest:
                continue
            prev = crop.filter(MarketPrice.market == latest.market,
                               MarketPrice.recorded_at < latest.recorded_at) \
                .order_by(MarketPrice.recorded_at.desc()).first()
            prices.append(_with_change({
                **seed,
                "variety": latest.variety or seed["variety"],
                "price": round(latest.price),
                "market": latest.market,
                "state": latest.state or seed["state"],
                "date": latest.recorded_at.date().isoformat(),
                "prev": prev.price if prev else None,
                "prev_date": prev.recorded_at.date().isoformat() if prev else None,
            }))
        return prices
    finally:
        db.close()


def _get_db_prices() -> list[dict]:
    with _lock:
        if _db_cache["prices"] is not None and time.time() - _db_cache["at"] < DB_CACHE_SECONDS:
            return _db_cache["prices"]
    try:
        prices = _prices_from_db()
    except Exception as e:
        logger.warning("Reading saved mandi prices failed (%s)", type(e).__name__)
        with _lock:
            return _db_cache["prices"] or []
    with _lock:
        _db_cache.update(prices=prices, at=time.time())
    return prices


def get_market_prices() -> list[dict]:
    """Latest live prices. Empty until the first refresh succeeds.
    With MARKET_PRICES_FROM_DB, the latest prices saved by scripts/update_prices.py."""
    if settings.MARKET_PRICES_FROM_DB:
        return _get_db_prices()
    start_price_refresh()
    with _lock:
        prices = _state["prices"]
    return prices or []


FORECAST_CACHE_SECONDS = 6 * 60 * 60   # prices change once a day
_forecast_cache: dict = {}             # crops -> (generated_at, forecast)


async def get_price_forecast(crops: list[str] = None) -> list[dict]:
    """AI-generated 30-day price forecast, cached. Serves the last forecast if Gemini is down."""
    target_crops = crops or ["Tomato", "Onion", "Wheat"]
    key = tuple(sorted(c.strip().lower() for c in target_crops))
    cached = _forecast_cache.get(key)
    if cached and time.time() - cached[0] < FORECAST_CACHE_SECONDS:
        return cached[1]

    current = {p["name"].lower(): p for p in get_market_prices()}
    # Forecast only crops with a live price; without one Gemini would invent it.
    target_crops = [current[c.strip().lower()]["name"] for c in target_crops if c.strip().lower() in current]
    if not target_crops:
        return []

    rag_docs = similarity_search("crop price forecast market India", n_results=2)
    rag_context = "\n".join([d["text"] for d in rag_docs])

    prompt = f"""
CURRENT MARKET PRICES (₹/quintal):
{chr(10).join([f"{c}: ₹{current[c.lower()]['price']} at {current[c.lower()]['market']}" for c in target_crops])}

MARKET KNOWLEDGE:
{rag_context}

Current month: {date.today():%B %Y}.

Generate 30-day price forecasts as JSON array:
[
  {{
    "crop": "Crop name",
    "current_price": 2285,
    "forecast_low": 2200,
    "forecast_high": 2400,
    "direction": "up|down|flat",
    "confidence": 78,
    "reason": "Brief market reason (max 8 words)"
  }}
]
Only forecast these crops: {target_crops}"""

    try:
        forecast = await generate_json(prompt, MARKET_SYSTEM)
    except GeminiUnavailableError:
        if cached:
            return cached[1]   # older than 6 hours, but better than an error
        raise
    if len(_forecast_cache) > 100:   # crop lists come from the client; keep memory bounded
        _forecast_cache.clear()
    _forecast_cache[key] = (time.time(), forecast)
    return forecast
