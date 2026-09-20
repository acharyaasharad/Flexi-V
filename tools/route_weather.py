from typing import Tuple, Optional
from models.weather_models import GeocodingResult, WeatherForecastResponse
from tools.geocoding import get_coordinates
from tools.weather_api import fetch_weather_forecast
from utils.logger import setup_logger

logger = setup_logger("route_weather_tool")

def get_location_and_weather(query: str) -> Tuple[Optional[GeocodingResult], Optional[WeatherForecastResponse]]:
    """Helper to orchestrate the geocoding and weather fetching flow."""
    logger.info(f"Routing request for query: {query}")
    
    geo = get_coordinates(query)
    if not geo:
        return None, None
        
    forecast = fetch_weather_forecast(geo)
    return geo, forecast
