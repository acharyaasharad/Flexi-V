import httpx
from typing import Optional
from config import OPEN_METEO_FORECAST_URL, REQUEST_TIMEOUT
from models.weather_models import GeocodingResult, WeatherForecastResponse
from utils.logger import setup_logger

logger = setup_logger("weather_api_tool")

def fetch_weather_forecast(geo: GeocodingResult) -> Optional[WeatherForecastResponse]:
    """Fetches hourly and daily weather forecast given geocoding results."""
    logger.info(f"Fetching forecast for {geo.name} ({geo.latitude}, {geo.longitude})")
    try:
        params = {
            "latitude": geo.latitude,
            "longitude": geo.longitude,
            "timezone": geo.timezone,
            "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,precipitation,weather_code,wind_speed_10m,wind_direction_10m,wind_gusts_10m,uv_index,cape",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,uv_index_max,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max",
            "models": "best_match"
        }
        
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.get(OPEN_METEO_FORECAST_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Simple wrapper mapping directly to Pydantic models
            return WeatherForecastResponse(**data)
            
    except Exception as e:
        logger.error(f"Error fetching forecast data: {str(e)}")
        return None
