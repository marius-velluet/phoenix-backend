import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OWM_API_KEY")

def get_wind_data(lat: float, lon: float) -> dict:
    """
    Récupère la vitesse et direction du vent pour des coordonnées GPS.
    """
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat":   lat,
            "lon":   lon,
            "appid": API_KEY,
            "units": "metric"  # vitesse en m/s
        }

        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        wind = {
            "vitesse_ms":  data["wind"]["speed"],
            "direction":   data["wind"].get("deg", 0),
        }

        print(f"📍 Lieu         : {data['name']}")
        print(f"💨 Vitesse vent : {wind['vitesse_ms']} m/s")
        print(f"🧭 Direction    : {wind['direction']}°")

        return wind

    except Exception as e:
        print(f"⚠️  Erreur API ({e}) — valeurs de repli activées")
        return {"vitesse_ms": 0.0, "direction": 0}


# Test sur le campus ESIEE Paris
if __name__ == "__main__":
    get_wind_data(48.84013163789159, 2.5837427716557353)