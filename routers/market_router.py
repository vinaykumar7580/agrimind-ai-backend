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

@router.get("/forecast")
async def price_forecast(crops: Optional[str] = Query(None)):
    crop_list = crops.split(",") if crops else None
    return await get_price_forecast(crop_list)

@router.get("/summary")
def market_summary():
    prices = get_market_prices()
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