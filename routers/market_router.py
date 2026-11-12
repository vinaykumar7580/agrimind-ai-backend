import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from database import get_db
from models import User, MarketPrice
from auth import get_current_user
from agents.market_agent import get_market_prices, get_price_forecast

router = APIRouter(prefix="/market", tags=["market"])

@router.get("/prices")
def market_prices(
    category: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    prices = get_market_prices()
    if category and category != "All":
        prices = [p for p in prices if p["category"] == category]
    if state:
        prices = [p for p in prices if p["state"] == state]
    return prices

# Each forecast is a Gemini call (free tier: 20 a day), and prices only change
# every few hours, so reuse a forecast for 6 hours.
FORECAST_TTL_SECONDS = 6 * 60 * 60
_forecast_cache: dict = {}

@router.get("/forecast")
async def price_forecast(crops: Optional[str] = Query(None)):
    crop_list = [c.strip() for c in crops.split(",") if c.strip()] if crops else None
    key = tuple(sorted(crop_list)) if crop_list else ()

    cached = _forecast_cache.get(key)
    if cached and time.time() - cached[0] < FORECAST_TTL_SECONDS:
        return cached[1]

    result = await get_price_forecast(crop_list)
    if len(_forecast_cache) > 50:   # crops is free text; keep the cache bounded
        _forecast_cache.clear()
    _forecast_cache[key] = (time.time(), result)
    return result

@router.get("/summary")
def market_summary():
    prices = get_market_prices()
    if not prices:   # no live prices yet
        return {"best_performer": None, "worst_performer": None, "average_price": None,
                "above_msp_count": 0, "total_crops": 0}
    best = max(prices, key=lambda x: x["change"])
    worst = min(prices, key=lambda x: x["change"])
    avg = round(sum(p["price"] for p in prices) / len(prices))
    above_msp = [p for p in prices if p.get("msp") and p["price"] >= p["msp"]]
    return {
        "best_performer": {"name": best["name"], "change": best["change"], "price": best["price"]},
        "worst_performer": {"name": worst["name"], "change": worst["change"], "price": worst["price"]},
        "average_price": avg,
        "above_msp_count": len(above_msp),
        "total_crops": len(prices),
    }