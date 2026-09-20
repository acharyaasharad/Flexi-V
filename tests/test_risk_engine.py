import pytest
from risk.risk_engine import evaluate_weather_risk
from models.weather_models import WeatherForecastResponse, HourlyWeather, DailyWeather

def create_mock_forecast(temp_max=20, rain_max=0, wind_max=10, cape_max=0):
    """Helper to generate a mock forecast response."""
    return WeatherForecastResponse(
        latitude=0.0,
        longitude=0.0,
        timezone="UTC",
        hourly=HourlyWeather(
            time=["2024-01-01T00:00"],
            temperature_2m=[temp_max],
            relative_humidity_2m=[50],
            apparent_temperature=[temp_max],
            precipitation=[rain_max],
            weather_code=[0],
            wind_speed_10m=[wind_max],
            wind_direction_10m=[0],
            wind_gusts_10m=[wind_max + 10],
            uv_index=[2],
            cape=[cape_max]
        ),
        daily=DailyWeather(
            time=["2024-01-01"],
            weather_code=[0],
            temperature_2m_max=[temp_max],
            temperature_2m_min=[temp_max - 5],
            sunrise=["2024-01-01T06:00"],
            sunset=["2024-01-01T18:00"],
            uv_index_max=[2],
            precipitation_sum=[rain_max],
            wind_speed_10m_max=[wind_max]
        )
    )

def test_no_risk():
    forecast = create_mock_forecast()
    signals = evaluate_weather_risk(forecast)
    assert len(signals) == 0

def test_extreme_heat_risk():
    forecast = create_mock_forecast(temp_max=46)
    signals = evaluate_weather_risk(forecast)
    assert any(s.parameter == "temperature" and s.level == "CRITICAL" for s in signals)

def test_heavy_rain_risk():
    forecast = create_mock_forecast(rain_max=35) # Extreme rain threshold is 30 in our config
    signals = evaluate_weather_risk(forecast)
    assert any(s.parameter == "precipitation" and s.level == "CRITICAL" for s in signals)

def test_high_wind_risk():
    forecast = create_mock_forecast(wind_max=65) # High wind threshold is 60
    signals = evaluate_weather_risk(forecast)
    assert any(s.parameter == "wind_speed" and s.level == "WARNING" for s in signals)
