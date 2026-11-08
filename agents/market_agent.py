import logging
import threading
import time
from datetime import date, datetime

import requests

from config import settings
from database import SessionLocal
from models import MarketPrice
from services.gemini_service import generate_json
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

# Tracked crops. Prices here are sample data, shown (with is_mock=True) until live
# prices arrive or when data.gov.in fails. MSP and category always come from here,
# because the feed does not include them. "market" is the preferred live mandi.
SEED_PRICES = [
    {"name": "Wheat", "variety": "HD-2967", "price": 2285, "prev": 2230, "msp": 2275, "market": "Pune APMC", "state": "Maharashtra", "category": "Cereals"},
    {"name": "Rice", "variety": "Basmati 1121", "price": 4850, "prev": 4910, "msp": 2300, "market": "Delhi Mandi", "state": "Delhi", "category": "Cereals"},
    {"name": "Soybean", "variety": "JS 9560", "price": 4620, "prev": 4450, "msp": 4600, "market": "Indore APMC", "state": "Madhya Pradesh", "category": "Oilseeds"},
    {"name": "Cotton", "variety": "Bt Cotton", "price": 6780, "prev": 6780, "msp": 7020, "market": "Nagpur Mandi", "state": "Maharashtra", "category": "Fibre"},
    {"name": "Sugarcane", "variety": "Co-86032", "price": 340, "prev": 336, "msp": 315, "market": "Kolhapur", "state": "Maharashtra", "category": "Cash Crops"},
    {"name": "Onion", "variety": "Nasik Red", "price": 1820, "prev": 1923, "msp": None, "market": "Lasalgaon", "state": "Maharashtra", "category": "Vegetables"},
    {"name": "Tomato", "variety": "Hybrid", "price": 2140, "prev": 1980, "msp": None, "market": "Nashik", "state": "Maharashtra", "category": "Vegetables"},
    {"name": "Maize", "variety": "Hybrid-10", "price": 2090, "prev": 2110, "msp": 2090, "market": "Nizamabad", "state": "Telangana", "category": "Cereals"},
    {"name": "Mustard", "variety": "Pusa Bold", "price": 5620, "prev": 5480, "msp": 5650, "market": "Alwar Mandi", "state": "Rajasthan", "category": "Oilseeds"},
    {"name": "Chana", "variety": "Desi", "price": 5350, "prev": 5300, "msp": 5440, "market": "Gulbarga", "state": "Karnataka", "category": "Pulses"},
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


def _sample_prices() -> list[dict]:
    return [_with_change({**p, "date": None, "is_mock": True}) for p in SEED_PRICES]


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


def _pick_record(seed: dict, records: list[dict]):
    """Latest price for a crop: the preferred mandi if it reported, else the median
    mandi in the crop's home state, else the median mandi nationally. The home state
    comes first because some states report far more mandis than others."""
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
    preferred = seed["market"].split()[0].lower()
    for row in rows:
        if preferred in str(row[2].get("market", "")).lower():
            return row
    home = [r for r in rows if str(r[2].get("state", "")).strip().lower() == seed["state"].lower()]
    rows = home or rows
    return rows[len(rows) // 2]


def _prev_price_and_save(db, row: dict, day: date):
    """Return the last stored price for this crop and mandi, and store today's."""
    day_start = datetime.combine(day, datetime.min.time())
    same = db.query(MarketPrice).filter(
        MarketPrice.crop_name == row["name"], MarketPrice.market == row["market"]
    )
    prev = same.filter(MarketPrice.recorded_at < day_start).order_by(MarketPrice.recorded_at.desc()).first()
    if not same.filter(MarketPrice.recorded_at == day_start).first():
        db.add(MarketPrice(
            crop_name=row["name"], variety=row["variety"], price=row["price"],
            prev_price=prev.price if prev else None, msp=row["msp"], market=row["market"],
            state=row["state"], category=row["category"], recorded_at=day_start,
        ))
    return prev.price if prev else None


def _build_live_prices(records: list[dict]) -> list[dict]:
    prices = []
    db = SessionLocal()
    try:
        for seed in SEED_PRICES:
            picked = _pick_record(seed, records)
            if not picked:
                logger.warning("No live mandi price for %s; showing its sample price", seed["name"])
                prices.append(_with_change({**seed, "date": None, "is_mock": True}))
                continue
            day, price, rec = picked
            row = {
                **seed,
                "variety": str(rec.get("variety") or "").strip() or seed["variety"],
                "price": round(price),
                "market": str(rec.get("market") or "").strip() or seed["market"],
                "state": str(rec.get("state") or "").strip() or seed["state"],
                "date": day.isoformat(),
                "is_mock": False,
            }
            row["prev"] = _prev_price_and_save(db, row, day)
            prices.append(_with_change(row))
        db.commit()
    finally:
        db.close()
    return prices


def _refresh():
    try:
        prices = _build_live_prices(_fetch_all_records())
        live = sum(not p["is_mock"] for p in prices)
        print(f"📈 Mandi prices refreshed: {live}/{len(prices)} crops live")
        with _lock:
            _state["prices"] = prices
            _state["next_refresh"] = time.time() + (REFRESH_SECONDS if live else RETRY_SECONDS)
    except Exception as e:
        # Log only the error type: request errors can include the URL with the API key.
        logger.warning("Mandi price refresh failed (%s); retrying in 30 minutes", type(e).__name__)
        with _lock:
            _state["next_refresh"] = time.time() + RETRY_SECONDS
    finally:
        with _lock:
            _state["refreshing"] = False


def start_price_refresh():
    """Refresh prices in the background if they are due. Never blocks."""
    if not settings.DATA_GOV_API_KEY:
        return
    with _lock:
        if _state["refreshing"] or time.time() < _state["next_refresh"]:
            return
        _state["refreshing"] = True
    threading.Thread(target=_refresh, daemon=True).start()


def get_market_prices() -> list[dict]:
    """Latest prices: live where available, otherwise sample prices with is_mock=True."""
    start_price_refresh()
    with _lock:
        prices = _state["prices"]
    return prices if prices is not None else _sample_prices()


async def get_price_forecast(crops: list[str] = None) -> list[dict]:
    """AI-generated 30-day price forecast."""
    target_crops = crops or ["Tomato", "Onion", "Wheat"]
    current = {p["name"]: p["price"] for p in get_market_prices()}

    rag_docs = similarity_search("crop price forecast market India", n_results=2)
    rag_context = "\n".join([d["text"] for d in rag_docs])

    prompt = f"""
CURRENT MARKET PRICES (₹/quintal):
{chr(10).join([f"{c}: ₹{current.get(c, 'N/A')}" for c in target_crops])}

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

    return await generate_json(prompt, MARKET_SYSTEM)
