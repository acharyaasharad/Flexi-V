import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# --- API Keys ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# --- Model Config ---
# Fallback to current fast model if not specified
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite")

# --- Open-Meteo Endpoints ---
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

# --- Request Timeouts ---
REQUEST_TIMEOUT = 10.0 # seconds

# --- Retry Logic ---
MAX_RETRIES = 3
INITIAL_BACKOFF = 2.0

# --- Risk Engine Thresholds ---
# These are basic thresholds. In a real system, these would be more complex and region-specific.
RISK_THRESHOLDS = {
    "high_wind_speed_kmh": 60.0,
    "extreme_wind_speed_kmh": 90.0,
    "heavy_rain_mm": 20.0, # per hour
    "extreme_rain_mm": 50.0, # per hour
    "high_temp_c": 38.0,
    "extreme_temp_c": 45.0,
    "low_temp_c": 0.0,
    "extreme_low_temp_c": -10.0,
    "high_uv_index": 8.0,
    "high_cape": 1500.0, # Convective Available Potential Energy (J/kg) indicating thunderstorm potential
}

# --- Source Priorities (For Tavily) ---
PRIORITIZED_SOURCES = [
    "imd.gov.in",       # India Meteorological Department
    "ndma.gov.in",      # National Disaster Management Authority (India)
    "weather.gov",      # National Weather Service (US)
    "nhc.noaa.gov",     # National Hurricane Center (US)
    "metoffice.gov.uk", # Met Office (UK)
]

# Validation
if not GEMINI_API_KEY:
    logging.warning("GEMINI_API_KEY is not set. Gemini features will fail.")
if not TAVILY_API_KEY:
    logging.warning("TAVILY_API_KEY is not set. Tavily web search will fail.")
