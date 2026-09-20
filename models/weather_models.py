from pydantic import BaseModel, Field
from typing import List, Optional

class GeocodingResult(BaseModel):
    name: str
    latitude: float
    longitude: float
    timezone: str
    country: str = "Unknown"
    admin1: str = "Unknown" # Region/State

class HourlyWeather(BaseModel):
    time: List[str]
    temperature_2m: List[float]
    relative_humidity_2m: List[float]
    apparent_temperature: List[float]
    precipitation_probability: Optional[List[int]] = None
    precipitation: List[float]
    weather_code: List[int]
    wind_speed_10m: List[float]
    wind_direction_10m: List[int]
    wind_gusts_10m: Optional[List[float]] = None
    uv_index: Optional[List[float]] = None
    cape: Optional[List[float]] = None

class DailyWeather(BaseModel):
    time: List[str]
    weather_code: List[int]
    temperature_2m_max: List[float]
    temperature_2m_min: List[float]
    sunrise: List[str]
    sunset: List[str]
    uv_index_max: Optional[List[float]] = None
    precipitation_sum: List[float]
    precipitation_probability_max: Optional[List[int]] = None
    wind_speed_10m_max: List[float]
    wind_gusts_10m_max: Optional[List[float]] = None

class WeatherForecastResponse(BaseModel):
    latitude: float
    longitude: float
    timezone: str
    hourly: HourlyWeather
    daily: DailyWeather
