import copy
from agent.weather_agent import get_weather_data
from risk.risk_engine import evaluate_weather_risk
from utils.formatting import format_risk_assessment_markdown
from models.risk_models import RiskAssessment

def run_what_if_simulation(location: str, delta_rain: float, delta_wind: float, delta_temp: float) -> str:
    """Runs a deterministic what-if scenario without using the LLM."""
    if not location.strip():
        return "Please run a location analysis first."
        
    geo, forecast = get_weather_data(location)
    if not geo or not forecast:
        return "Could not load forecast for simulation."
        
    # Deep copy so we don't mutate the original cache if we had one
    sim_forecast = copy.deepcopy(forecast)
    
    # Apply Deltas
    if sim_forecast.hourly:
        if sim_forecast.hourly.precipitation and delta_rain > 0:
            sim_forecast.hourly.precipitation = [x + delta_rain for x in sim_forecast.hourly.precipitation]
            
        if sim_forecast.hourly.wind_speed_10m and delta_wind > 0:
            sim_forecast.hourly.wind_speed_10m = [x + delta_wind for x in sim_forecast.hourly.wind_speed_10m]
            if sim_forecast.hourly.wind_gusts_10m:
                sim_forecast.hourly.wind_gusts_10m = [x + delta_wind for x in sim_forecast.hourly.wind_gusts_10m]
                
        if sim_forecast.hourly.temperature_2m and delta_temp != 0:
            sim_forecast.hourly.temperature_2m = [x + delta_temp for x in sim_forecast.hourly.temperature_2m]

    # Evaluate with deterministic engine
    signals, overall_score, hourly_scores, peak_window, primary_risk = evaluate_weather_risk(sim_forecast)
    
    overall_level = "LOW"
    if overall_score >= 80: overall_level = "CRITICAL"
    elif overall_score >= 60: overall_level = "HIGH"
    elif overall_score >= 40: overall_level = "MODERATE"
    
    # Build simulated assessment struct
    assessment = RiskAssessment(
        location_name=f"{geo.name} (SIMULATED)",
        overall_risk_level=overall_level,
        overall_risk_score=overall_score,
        primary_risk=primary_risk,
        peak_risk_window=peak_window,
        confidence_score=100.0, # Deterministic logic has 100% confidence in its math
        signals=signals,
        summary=f"This is a simulated scenario applying: +{delta_rain}mm rain, +{delta_wind}km/h wind, {delta_temp}°C temp.",
        recommendations=["Simulation only. Refer to actual forecast for real-world guidance."],
        sources=[],
        hourly_risk_scores=hourly_scores,
        is_deterministic_fallback=False
    )
    
    return format_risk_assessment_markdown(assessment.model_dump())
