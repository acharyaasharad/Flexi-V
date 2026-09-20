from typing import List, Tuple
from models.weather_models import WeatherForecastResponse
from models.risk_models import RiskSignal
from risk.risk_rules import DEFAULT_THRESHOLDS, calculate_parameter_score, calculate_inverse_parameter_score
from utils.logger import setup_logger

logger = setup_logger("risk_engine")

def evaluate_weather_risk(forecast: WeatherForecastResponse) -> Tuple[List[RiskSignal], float, List[float], str, str]:
    """
    Deterministically evaluates weather forecast data.
    Returns:
    - signals: List of RiskSignal objects
    - overall_risk_score: 0-100 float
    - hourly_scores: List of float (0-100) for each hour
    - peak_risk_window: string describing the time of highest risk
    - primary_risk_category: string
    """
    logger.info("Evaluating hourly weather risk deterministically...")
    signals = []
    
    if not forecast or not forecast.hourly:
        return signals, 0.0, [], "None", "None"

    # Analyze next 48 hours
    limit = min(48, len(forecast.hourly.time))
    
    hourly_scores = []
    max_scores = {
        "wind_speed": 0.0,
        "temperature": 0.0,
        "precipitation": 0.0,
        "uv_index": 0.0,
        "cape": 0.0
    }
    
    max_values = {
        "wind_speed": 0.0,
        "temperature_high": 0.0,
        "temperature_low": 999.0,
        "precipitation": 0.0,
        "uv_index": 0.0,
        "cape": 0.0
    }

    peak_hour_idx = 0
    max_hourly_score = 0.0

    for i in range(limit):
        time = forecast.hourly.time[i]
        wind = max(forecast.hourly.wind_speed_10m[i] if forecast.hourly.wind_speed_10m else 0, 
                   forecast.hourly.wind_gusts_10m[i] if forecast.hourly.wind_gusts_10m else 0)
        temp = forecast.hourly.temperature_2m[i] if forecast.hourly.temperature_2m else 0
        rain = forecast.hourly.precipitation[i] if forecast.hourly.precipitation else 0
        uv = forecast.hourly.uv_index[i] if forecast.hourly.uv_index else 0
        cape = forecast.hourly.cape[i] if forecast.hourly.cape else 0

        # Update max actual values
        max_values["wind_speed"] = max(max_values["wind_speed"], wind)
        max_values["temperature_high"] = max(max_values["temperature_high"], temp)
        max_values["temperature_low"] = min(max_values["temperature_low"], temp)
        max_values["precipitation"] = max(max_values["precipitation"], rain)
        max_values["uv_index"] = max(max_values["uv_index"], uv)
        max_values["cape"] = max(max_values["cape"], cape)

        # Calculate scores for this hour
        w_score = calculate_parameter_score(wind, DEFAULT_THRESHOLDS.high_wind_speed_kmh, DEFAULT_THRESHOLDS.extreme_wind_speed_kmh)
        t_high_score = calculate_parameter_score(temp, DEFAULT_THRESHOLDS.high_temp_c, DEFAULT_THRESHOLDS.extreme_temp_c)
        t_low_score = calculate_inverse_parameter_score(temp, DEFAULT_THRESHOLDS.low_temp_c, DEFAULT_THRESHOLDS.extreme_low_temp_c)
        t_score = max(t_high_score, t_low_score)
        
        r_score = calculate_parameter_score(rain, DEFAULT_THRESHOLDS.heavy_rain_mm, DEFAULT_THRESHOLDS.extreme_rain_mm)
        u_score = calculate_parameter_score(uv, DEFAULT_THRESHOLDS.high_uv_index, DEFAULT_THRESHOLDS.extreme_uv_index)
        c_score = calculate_parameter_score(cape, DEFAULT_THRESHOLDS.high_cape, DEFAULT_THRESHOLDS.extreme_cape)
        
        # Hourly combined score (weighted sum or max - using a mix)
        # We take the max of the primary threats + small additive for compounding threats
        scores = [w_score, t_score, r_score, u_score, c_score]
        scores.sort(reverse=True)
        hour_score = min(100.0, scores[0] + (scores[1] * 0.2) if len(scores) > 1 else scores[0])
        hourly_scores.append(hour_score)
        
        if hour_score > max_hourly_score:
            max_hourly_score = hour_score
            peak_hour_idx = i

        # Track max scores for signals
        max_scores["wind_speed"] = max(max_scores["wind_speed"], w_score)
        max_scores["temperature"] = max(max_scores["temperature"], t_score)
        max_scores["precipitation"] = max(max_scores["precipitation"], r_score)
        max_scores["uv_index"] = max(max_scores["uv_index"], u_score)
        max_scores["cape"] = max(max_scores["cape"], c_score)

    # Build peak window string (Peak hour +/- 2 hours)
    start_idx = max(0, peak_hour_idx - 2)
    end_idx = min(limit - 1, peak_hour_idx + 2)
    
    try:
        # e.g., "2023-10-27T14:00" -> "14:00"
        def format_time(t_str): return t_str.split("T")[1] if "T" in t_str else t_str
        peak_time_start = format_time(forecast.hourly.time[start_idx])
        peak_time_end = format_time(forecast.hourly.time[end_idx])
        peak_date = forecast.hourly.time[peak_hour_idx].split("T")[0]
        peak_risk_window = f"{peak_date} {peak_time_start} - {peak_time_end}"
    except Exception:
        peak_risk_window = "Unknown"

    # Determine primary risk
    primary_risk_category = "None"
    max_cat_score = 0
    for cat, score in max_scores.items():
        if score > max_cat_score:
            max_cat_score = score
            primary_risk_category = cat.replace("_", " ").title()

    # Generate explicit signals
    if max_scores["wind_speed"] >= 80:
        signals.append(RiskSignal(parameter="wind_speed", level="CRITICAL", message="Extreme wind speeds or gusts detected. Risk of structural damage and power outages.", value=max_values["wind_speed"], threshold=DEFAULT_THRESHOLDS.extreme_wind_speed_kmh, severity_score=max_scores["wind_speed"]))
    elif max_scores["wind_speed"] >= 40:
        signals.append(RiskSignal(parameter="wind_speed", level="WARNING", message="High wind speeds detected.", value=max_values["wind_speed"], threshold=DEFAULT_THRESHOLDS.high_wind_speed_kmh, severity_score=max_scores["wind_speed"]))

    if max_scores["precipitation"] >= 80:
        signals.append(RiskSignal(parameter="precipitation", level="CRITICAL", message="Extreme heavy rainfall expected. High risk of flash flooding.", value=max_values["precipitation"], threshold=DEFAULT_THRESHOLDS.extreme_rain_mm, severity_score=max_scores["precipitation"]))
    elif max_scores["precipitation"] >= 40:
        signals.append(RiskSignal(parameter="precipitation", level="WARNING", message="Heavy rainfall expected. Potential for localized flooding.", value=max_values["precipitation"], threshold=DEFAULT_THRESHOLDS.heavy_rain_mm, severity_score=max_scores["precipitation"]))
        
    if max_scores["temperature"] >= 80:
        val = max_values["temperature_high"] if max_values["temperature_high"] >= DEFAULT_THRESHOLDS.extreme_temp_c else max_values["temperature_low"]
        thresh = DEFAULT_THRESHOLDS.extreme_temp_c if max_values["temperature_high"] >= DEFAULT_THRESHOLDS.extreme_temp_c else DEFAULT_THRESHOLDS.extreme_low_temp_c
        msg = "Extreme heat conditions." if max_values["temperature_high"] >= DEFAULT_THRESHOLDS.extreme_temp_c else "Extreme cold conditions."
        signals.append(RiskSignal(parameter="temperature", level="CRITICAL", message=msg, value=val, threshold=thresh, severity_score=max_scores["temperature"]))
    elif max_scores["temperature"] >= 40:
        val = max_values["temperature_high"] if max_values["temperature_high"] >= DEFAULT_THRESHOLDS.high_temp_c else max_values["temperature_low"]
        thresh = DEFAULT_THRESHOLDS.high_temp_c if max_values["temperature_high"] >= DEFAULT_THRESHOLDS.high_temp_c else DEFAULT_THRESHOLDS.low_temp_c
        msg = "High heat conditions." if max_values["temperature_high"] >= DEFAULT_THRESHOLDS.high_temp_c else "Freezing conditions."
        signals.append(RiskSignal(parameter="temperature", level="WARNING", message=msg, value=val, threshold=thresh, severity_score=max_scores["temperature"]))

    if max_scores["cape"] >= 40:
        signals.append(RiskSignal(parameter="cape", level="WARNING", message="High atmospheric instability. Increased potential for severe thunderstorms.", value=max_values["cape"], threshold=DEFAULT_THRESHOLDS.high_cape, severity_score=max_scores["cape"]))

    overall_risk_score = round(max_hourly_score, 1)

    logger.info(f"Calculated overall risk score: {overall_risk_score}/100. Peak Window: {peak_risk_window}")
    return signals, overall_risk_score, hourly_scores, peak_risk_window, primary_risk_category
