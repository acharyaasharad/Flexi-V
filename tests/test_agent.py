import pytest
from unittest.mock import patch, MagicMock
from models.weather_models import WeatherForecastResponse, HourlyWeather, DailyWeather, GeocodingResult
from risk.risk_engine import evaluate_weather_risk
from agent.gemini_agent import synthesize_risk_report
from models.agent_models import AgentContext
from google.genai.errors import APIError

def get_dummy_forecast():
    """Returns a safe baseline forecast."""
    return WeatherForecastResponse(
        latitude=0.0,
        longitude=0.0,
        timezone="UTC",
        hourly=HourlyWeather(
            time=[f"2023-10-27T{i:02d}:00" for i in range(48)],
            temperature_2m=[20.0] * 48,
            relative_humidity_2m=[50.0] * 48,
            apparent_temperature=[20.0] * 48,
            precipitation=[0.0] * 48,
            weather_code=[0] * 48,
            wind_speed_10m=[10.0] * 48,
            wind_direction_10m=[180] * 48,
            wind_gusts_10m=[15.0] * 48,
        uv_index=[0.0] * 48,
        cape=[100.0] * 48
        ),
        daily=DailyWeather(
            time=["2023-10-27", "2023-10-28"],
            weather_code=[0, 0],
            temperature_2m_max=[25.0, 25.0],
            temperature_2m_min=[15.0, 15.0],
            sunrise=["2023-10-27T06:00", "2023-10-28T06:00"],
            sunset=["2023-10-27T18:00", "2023-10-28T18:00"],
            precipitation_sum=[0.0, 0.0],
            wind_speed_10m_max=[15.0, 15.0]
        )
    )

def test_risk_engine_low_risk():
    forecast = get_dummy_forecast()
    signals, overall_score, hourly, peak, primary = evaluate_weather_risk(forecast)
    assert len(signals) == 0
    assert overall_score < 40.0
    assert primary == "None"

def test_risk_engine_extreme_wind():
    forecast = get_dummy_forecast()
    # Insert extreme wind at hour 14
    forecast.hourly.wind_speed_10m[14] = 95.0
    forecast.hourly.wind_gusts_10m[14] = 110.0
    
    signals, overall_score, hourly, peak, primary = evaluate_weather_risk(forecast)
    assert len(signals) > 0
    assert any(s.parameter == "wind_speed" and s.level == "CRITICAL" for s in signals)
    assert overall_score >= 80.0
    assert primary == "Wind Speed"
    assert "12:00" in peak

@patch("agent.gemini_agent.genai.Client")
@patch("agent.gemini_agent.time.sleep")
def test_gemini_503_fallback(mock_sleep, mock_client):
    """Test that a 503 error correctly triggers the deterministic fallback."""
    # Setup mock to raise APIError 503 every time
    mock_models = MagicMock()
    # Mocking the google.genai.errors.APIError which takes a message and code
    error = APIError("503 Service Unavailable", 503, "UNAVAILABLE")
    mock_models.generate_content.side_effect = error
    
    mock_client_instance = MagicMock()
    mock_client_instance.models = mock_models
    mock_client.return_value = mock_client_instance
    
    # Create context
    context = AgentContext(query="Miami")
    context.geocoding = GeocodingResult(name="Miami", latitude=25.7, longitude=-80.1, timezone="EST")
    context.chat_history = [{"role": "system", "content": "Overall Risk Level: CRITICAL"}]
    
    response = synthesize_risk_report(context)
    
    # Verify fallback kicked in
    assert response.structured_risk is not None
    assert response.structured_risk["is_deterministic_fallback"] is True
    assert response.structured_risk["overall_risk_level"] == "CRITICAL"
    assert "AI SYNTHESIS TEMPORARILY UNAVAILABLE" in response.structured_risk["summary"]
    # Verify retry backoff sleep was called
    assert mock_sleep.called
