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

df = pd.DataFrame(weather_data)
df["Weather Description"] = df["Weather Code"].map(wmo_weather_codes)
df["Weather Description"] = df["Weather Description"].fillna("Unknown")

num_df = df.select_dtypes(include='number')
avg_df = df.groupby("City")[num_df.columns].mean().reset_index()

df = df.drop_duplicates(subset=['Date/Time', 'City'])

# temperature trends
sns.set(style="whitegrid")
plt.figure(figsize=(10, 6))
ax = sns.lineplot(data=df, x="Date/Time", y="Temperature (°C)", hue="City")

unique = df["Date/Time"].unique()
temp = unique[::12]
ax.set_xticks(range(0, len(unique), 12))
ax.set_xticklabels(temp, rotation=45)

plt.title("Temperature (°C) Trends Over Time")
plt.xlabel("Date/Time")
plt.ylabel("Temperature (°C)")
plt.tight_layout()
plt.savefig("temperature_trends.png")
plt.close()

# average humidity
plt.figure(figsize=(8, 6))
sns.barplot(x="City", y="Humidity", data=avg_df)
plt.title("Average Humidity by City")
plt.xlabel("City")
plt.ylabel("Humidity (%)")
plt.savefig("average_humidity.png")
plt.close()

# heat map
pivot_df = df.pivot(index="City", columns="Date/Time", values="Temperature (°C)")
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

# weather description
threshold = 0.05  # for 'other' category
weather_freq = df["Weather Description"].value_counts()
weather_freq = weather_freq / weather_freq.sum()
other_freq = weather_freq[weather_freq < threshold].sum()
weather_freq = weather_freq[weather_freq >= threshold]
weather_freq["Other"] = other_freq

plt.figure(figsize=(8, 6))
weather_freq.plot.pie(autopct='%1.1f%%', startangle=90, labels=weather_freq.index)
plt.title("Weather Description Frequency")
plt.ylabel('')
plt.savefig("weather_description_frequency.png")
plt.close()