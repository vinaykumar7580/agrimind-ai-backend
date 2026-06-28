from fastapi import APIRouter, Depends, Query
from models import User
from auth import get_current_user
from agents.weather_agent import get_weather

router = APIRouter(prefix="/weather", tags=["weather"])

@router.get("/")
async def weather(
    district: str = Query(None),
    state: str = Query(None),
    current_user: User = Depends(get_current_user)
):
    d = district or current_user.district or "Pune"
    s = state or current_user.state or "Maharashtra"
    return await get_weather(d, s)

@router.get("/advisory")
async def advisory(current_user: User = Depends(get_current_user)):
    d = current_user.district or "Pune"
    s = current_user.state or "Maharashtra"
    data = await get_weather(d, s)
    return {"advisory": data["advisory"], "gdd_today": data.get("gdd_today")}