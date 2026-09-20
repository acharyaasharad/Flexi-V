from typing import Tuple, Optional
from models.weather_models import GeocodingResult, WeatherForecastResponse
from tools.route_weather import get_location_and_weather

def get_weather_data(query: str) -> Tuple[Optional[GeocodingResult], Optional[WeatherForecastResponse]]:
    """Agentic wrapper to gather weather data."""
    return get_location_and_weather(query)
