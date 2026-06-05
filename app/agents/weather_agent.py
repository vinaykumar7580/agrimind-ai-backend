from app.services.weather_service import get_weather

def weather_agent(city):

    data = get_weather(city)

    return {
        "temperature": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "wind_speed": data["wind"]["speed"]
    }