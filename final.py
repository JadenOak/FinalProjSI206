import requests
import pandas as pd
import sqlite3
import seaborn as sns
import matplotlib.pyplot as plt

cities = {
    "Ann Arbor": (42.2808, -83.7430),
    "Detroit": (42.3314, -83.0458),
    "East Lansing": (42.7360, -84.4839),
    "Royal Oak": (42.4895, -83.1446),
    "Flint": (43.0125, -83.6875),
    "Grand Rapids": (42.9634, -85.6681),
    "Traverse City": (44.7631, -85.6206),
}

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

def fetch_weather_data(latitude, longitude):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&timezone=America%2FNew_York"
    response = requests.get(url)
    return response.json()

def fetch_air_quality_data(latitude, longitude):
    url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={latitude}&longitude={longitude}&hourly=pm10,pm2_5,ozone&forecast_days=7&domains=cams_global"
    response = requests.get(url)
    return response.json()

weather_data = []

for city, (lat, lon) in cities.items():
    data = fetch_weather_data(lat, lon)['hourly']
    for i, time in enumerate(data["time"]):
        weather_data.append({
            "City": city,
            "Date/Time": time,
            "Temperature (°C)": data["temperature_2m"][i],
            "Humidity": data["relative_humidity_2m"][i],
            "Wind Speed": data["wind_speed_10m"][i],
            "Weather Code": data["weather_code"][i]
        })

weather_df = pd.DataFrame(weather_data)

weather_conn = sqlite3.connect("weather_forecast.db")
weather_df.to_sql("weather_data", weather_conn, if_exists="replace", index=False)
weather_conn.close()

air_quality_data = []

for city, (lat, lon) in cities.items():
    data = fetch_air_quality_data(lat, lon)['hourly']
    for i, time in enumerate(data["time"]):
        air_quality_data.append({
            "City": city,
            "Date/Time": time,
            "PM10": data["pm10"][i],
            "PM2_5": data["pm2_5"][i],
            "Ozone": data["ozone"][i]
        })

air_quality_df = pd.DataFrame(air_quality_data)

air_quality_conn = sqlite3.connect("air_quality.db")
air_quality_df.to_sql("air_quality_data", air_quality_conn, if_exists="replace", index=False)
air_quality_conn.close()
weather_conn = sqlite3.connect("weather_forecast.db")
air_quality_conn = sqlite3.connect("air_quality.db")
combined_conn = sqlite3.connect("combined_weather_air_quality.db")

weather_df = pd.read_sql("SELECT * FROM weather_data", weather_conn)
weather_df.to_sql("weather_data", combined_conn, if_exists="replace", index=False)
air_quality_df = pd.read_sql("SELECT * FROM air_quality_data", air_quality_conn)
air_quality_df.to_sql("air_quality_data", combined_conn, if_exists="replace", index=False)

weather_conn.close()
air_quality_conn.close()

# join query
query = """
SELECT 
    w.*, 
    a.PM10, 
    a.PM2_5, 
    a.Ozone
FROM weather_data w 
JOIN air_quality_data a 
ON w.City = a.City AND w."Date/Time" = a."Date/Time"
"""

# joined data
result_df = pd.read_sql(query, combined_conn)
combined_conn.close()
result_df['City'] = result_df['City'].astype(str)

num_df = result_df.select_dtypes(include='number')
avg_df = result_df.groupby("City")[num_df.columns].mean().reset_index()
result_df = result_df.drop_duplicates(subset=['Date/Time', 'City'])

# temp line graph
sns.set(style="whitegrid")
plt.figure(figsize=(10, 6))
ax = sns.lineplot(data=result_df, x="Date/Time", y="Temperature (°C)", hue="City")

unique = result_df["Date/Time"].unique()
temp = unique[::12]
ax.set_xticks(range(0, len(unique), 12))
ax.set_xticklabels(temp, rotation=45)

plt.title("Temperature (°C) Trends Over Time")
plt.xlabel("Date/Time")
plt.ylabel("Temperature (°C)")
plt.tight_layout()
plt.savefig("temperature_trends.png")
plt.close()

# avg humidity
plt.figure(figsize=(8, 6))
sns.barplot(x="City", y="Humidity", data=avg_df)
plt.title("Average Humidity by City")
plt.xlabel("City")
plt.ylabel("Humidity (%)")
plt.savefig("average_humidity.png")
plt.close()

# heat map
pivot_df = result_df.pivot(index="City", columns="Date/Time", values="Temperature (°C)")
plt.figure(figsize=(12, 6))
heatmap_ax = sns.heatmap(pivot_df, cmap="coolwarm", annot=False)
heatmap_ax.set_xticks(range(0, len(pivot_df.columns), 12))
heatmap_ax.set_xticklabels(pivot_df.columns[::12], rotation=45)

plt.title("Temperature (°C) Comparison Over Time Between Cities")
plt.xlabel("Date/Time")
plt.ylabel("City")
plt.tight_layout()
plt.savefig("temperature_heatmap.png")
plt.close()

# pm2.5 air qual
plt.figure(figsize=(10, 6))
ax = sns.lineplot(data=result_df, x="Date/Time", y="PM2_5", hue="City")
ax.set_xticks(range(0, len(unique), 12))
ax.set_xticklabels(temp, rotation=45)

plt.title("PM2.5 Trends Over Time")
plt.xlabel("Date/Time")
plt.ylabel("PM2.5 Levels (µg/m³)")
plt.tight_layout()
plt.savefig("pm25_trends.png")
plt.close()

# pm10 air qual
plt.figure(figsize=(8, 6))
sns.barplot(x="City", y="PM10", data=avg_df)
plt.title("Average PM10 Levels by City")
plt.xlabel("City")
plt.ylabel("PM10 Levels (µg/m³)")
plt.savefig("average_pm10.png")
plt.close()

result_df["Weather Description"] = result_df["Weather Code"].map(wmo_weather_codes)
result_df["Weather Description"] = result_df["Weather Description"].fillna("Unknown")

threshold = 0.05  # for 'other' category
weather_freq = result_df["Weather Description"].value_counts()
weather_freq = weather_freq / weather_freq.sum()
other_freq = weather_freq[weather_freq < threshold].sum()
weather_freq = weather_freq[weather_freq >= threshold]
weather_freq["Other"] = other_freq

plt.figure(figsize=(8, 6))
weather_freq.plot.pie(autopct='%.1f%%', startangle=90, labels=weather_freq.index)
plt.title("Weather Description Frequency")
plt.ylabel('')
plt.savefig("weather_description_frequency.png")
plt.close()
