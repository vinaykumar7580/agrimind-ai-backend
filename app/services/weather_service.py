import requests
import os

API_KEY = os.getenv("OPENWEATHER_API_KEY")

def get_weather(city):

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    response = requests.get(
        url,
        params=params
    )

    return response.json()