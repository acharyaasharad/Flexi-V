import httpx
from typing import Optional
from config import OPEN_METEO_GEOCODING_URL, REQUEST_TIMEOUT
from models.weather_models import GeocodingResult
from utils.logger import setup_logger

logger = setup_logger("geocoding_tool")

def get_coordinates(location_name: str) -> Optional[GeocodingResult]:
    """Fetches geocoding data for a given location name."""
    logger.info(f"Geocoding requested for: {location_name}")
    try:
        params = {
            "name": location_name,
            "count": 1,
            "language": "en",
            "format": "json"
        }
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.get(OPEN_METEO_GEOCODING_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "results" in data and len(data["results"]) > 0:
                result = data["results"][0]
                return GeocodingResult(
                    name=result.get("name"),
                    latitude=result.get("latitude"),
                    longitude=result.get("longitude"),
                    timezone=result.get("timezone", "UTC"),
                    country=result.get("country", "Unknown"),
                    admin1=result.get("admin1", "Unknown")
                )
            else:
                logger.warning(f"No geocoding results found for {location_name}")
                return None
    except Exception as e:
        logger.error(f"Error during geocoding: {str(e)}")
        return None
