import requests
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def fetch_weather_data(latitude, longitude):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&timezone=America%2FNew_York"
    response = requests.get(url)
    return response.json()

wmo_weather_codes = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Light rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Light snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Rain showers",
    81: "Moderate rain showers",
    82: "Heavy rain showers",
    85: "Snow showers",
    95: "Thunderstorm",
}

cities = {
    "Ann Arbor": (42.2808, -83.7430),
    "Detroit": (42.3314, -83.0458),
    "East Lansing": (42.7360, -84.4839),
    "Royal Oak": (42.4895, -83.1446),
    "Flint": (43.0125, -83.6875),
    "Grand Rapids": (42.9634, -85.6681),
    "Traverse City": (44.7631, -85.6206),
}

weather_data = []

for city, (lat, lon) in cities.items():
    # fetch data from api
    data = fetch_weather_data(lat, lon)
    hourly = data['hourly']
    for i, time in enumerate(hourly["time"]):
        weather_data.append({
            "City": city,
            "Date/Time": time,
            "Temperature (°C)": hourly["temperature_2m"][i],
            "Humidity": hourly["relative_humidity_2m"][i],
            "Wind Speed": hourly["wind_speed_10m"][i],
            "Weather Code": hourly["weather_code"][i]
        })

