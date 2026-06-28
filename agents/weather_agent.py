import httpx
from services.ollama_service import generate
from config import settings

async def get_weather(district: str, state: str, lat: float = None, lon: float = None) -> dict:
    """Fetch weather and generate farm advisory."""

    weather_data = {}

    # Fetch from OpenWeatherMap if API key set
    if settings.OPENWEATHER_API_KEY:
        try:
            query = f"{district},{state},IN"
            async with httpx.AsyncClient(timeout=10) as client:
                # Current weather
                cur = await client.get(
                    "https://api.openweathermap.org/data/2.5/weather",
                    params={"q": query, "appid": settings.OPENWEATHER_API_KEY, "units": "metric"}
                )
                if cur.status_code == 200:
                    cw = cur.json()
                    weather_data["current"] = {
                        "temp_c": round(cw["main"]["temp"]),
                        "feels_like": round(cw["main"]["feels_like"]),
                        "humidity": cw["main"]["humidity"],
                        "wind_kmh": round(cw["wind"]["speed"] * 3.6),
                        "condition": cw["weather"][0]["description"].title(),
                        "visibility_km": round(cw.get("visibility", 8000) / 1000),
                        "rain_chance": cw.get("rain", {}).get("1h", 0) * 100,
                    }

                # 7-day forecast
                fct = await client.get(
                    "https://api.openweathermap.org/data/2.5/forecast",
                    params={"q": query, "appid": settings.OPENWEATHER_API_KEY, "units": "metric", "cnt": 7}
                )
                if fct.status_code == 200:
                    days = []
                    for item in fct.json()["list"][:7]:
                        days.append({
                            "day": item["dt_txt"][:10],
                            "temp": round(item["main"]["temp"]),
                            "rain": round(item.get("pop", 0) * 100),
                            "condition": item["weather"][0]["main"]
                        })
                    weather_data["forecast"] = days
        except Exception as e:
            print(f"Weather API error: {e}")

    # Fallback mock data
    if not weather_data:
        weather_data = {
            "current": {
                "temp_c": 31, "feels_like": 34, "humidity": 72,
                "wind_kmh": 14, "condition": "Partly Cloudy",
                "visibility_km": 8, "rain_chance": 20
            },
            "forecast": [
                {"day": "Mon", "temp": 32, "rain": 5, "condition": "Clear"},
                {"day": "Tue", "temp": 28, "rain": 30, "condition": "Clouds"},
                {"day": "Wed", "temp": 24, "rain": 75, "condition": "Rain"},
                {"day": "Thu", "temp": 22, "rain": 85, "condition": "Rain"},
                {"day": "Fri", "temp": 27, "rain": 20, "condition": "Clouds"},
                {"day": "Sat", "temp": 31, "rain": 5, "condition": "Clear"},
                {"day": "Sun", "temp": 33, "rain": 0, "condition": "Clear"},
            ]
        }

    # Generate farm advisory
    advisory_prompt = f"""
You are an agricultural weather advisor for Indian farmers.
Current weather in {district}, {state}:
Temperature: {weather_data['current']['temp_c']}°C
Humidity: {weather_data['current']['humidity']}%
Wind: {weather_data['current']['wind_kmh']} km/h
Rain chance: {weather_data['current']['rain_chance']}%
7-day forecast: {weather_data.get('forecast', [])}

Write a 2-3 sentence farm advisory in simple English. Cover:
- Best time for spraying/fertilizer application
- Irrigation advice
- Any weather warnings for crops
Keep it practical and specific."""

    advisory = await generate(advisory_prompt)
    weather_data["advisory"] = advisory

    # Calculate GDD (Growing Degree Days) — base temp 10°C
    base_temp = 10
    temp = weather_data["current"]["temp_c"]
    gdd_today = max(0, temp - base_temp)
    weather_data["gdd_today"] = round(gdd_today, 1)

    return weather_data