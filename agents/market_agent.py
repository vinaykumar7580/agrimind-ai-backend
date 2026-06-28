from services.ollama_service import generate_json
from rag.vector_store import similarity_search

MARKET_SYSTEM = """You are AgriMind's agricultural market analyst specializing in Indian commodity markets and APMC mandis.
Respond ONLY in valid JSON."""

# Seeded market data (in production, pull from Agmarknet API)
SEED_PRICES = [
    {"name": "Wheat", "variety": "HD-2967", "price": 2285, "prev": 2230, "msp": 2275, "market": "Pune APMC", "state": "Maharashtra", "category": "Cereals"},
    {"name": "Rice", "variety": "Basmati 1121", "price": 4850, "prev": 4910, "msp": 2300, "market": "Delhi Mandi", "state": "Delhi", "category": "Cereals"},
    {"name": "Soybean", "variety": "JS 9560", "price": 4620, "prev": 4450, "msp": 4600, "market": "Indore APMC", "state": "MP", "category": "Oilseeds"},
    {"name": "Cotton", "variety": "Bt Cotton", "price": 6780, "prev": 6780, "msp": 7020, "market": "Nagpur Mandi", "state": "Maharashtra", "category": "Fibre"},
    {"name": "Sugarcane", "variety": "Co-86032", "price": 340, "prev": 336, "msp": 315, "market": "Kolhapur", "state": "Maharashtra", "category": "Cash Crops"},
    {"name": "Onion", "variety": "Nasik Red", "price": 1820, "prev": 1923, "msp": None, "market": "Lasalgaon", "state": "Maharashtra", "category": "Vegetables"},
    {"name": "Tomato", "variety": "Hybrid", "price": 2140, "prev": 1980, "msp": None, "market": "Nashik", "state": "Maharashtra", "category": "Vegetables"},
    {"name": "Maize", "variety": "Hybrid-10", "price": 2090, "prev": 2110, "msp": 2090, "market": "Nizamabad", "state": "Telangana", "category": "Cereals"},
    {"name": "Mustard", "variety": "Pusa Bold", "price": 5620, "prev": 5480, "msp": 5650, "market": "Alwar Mandi", "state": "Rajasthan", "category": "Oilseeds"},
    {"name": "Chana", "variety": "Desi", "price": 5350, "prev": 5300, "msp": 5440, "market": "Gulbarga", "state": "Karnataka", "category": "Pulses"},
]

def get_market_prices() -> list[dict]:
    """Return prices with calculated change %."""
    prices = []
    for p in SEED_PRICES:
        change = round((p["price"] - p["prev"]) / p["prev"] * 100, 1)
        trend = "up" if change > 0 else "down" if change < 0 else "flat"
        msp_diff = round((p["price"] - p["msp"]) / p["msp"] * 100, 1) if p["msp"] else None
        prices.append({**p, "change": change, "trend": trend, "msp_diff": msp_diff})
    return prices

async def get_price_forecast(crops: list[str] = None) -> list[dict]:
    """AI-generated 30-day price forecast."""
    target_crops = crops or ["Tomato", "Onion", "Wheat"]
    current = {p["name"]: p["price"] for p in SEED_PRICES}

    rag_docs = similarity_search("crop price forecast market India", n_results=2)
    rag_context = "\n".join([d["text"] for d in rag_docs])

    prompt = f"""
CURRENT MARKET PRICES (₹/quintal):
{chr(10).join([f"{c}: ₹{current.get(c, 'N/A')}" for c in target_crops])}

MARKET KNOWLEDGE:
{rag_context}

Current month: June 2026, Kharif sowing season.

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