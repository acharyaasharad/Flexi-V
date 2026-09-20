from pydantic import BaseModel

class RiskThresholds(BaseModel):
    # Wind (km/h)
    high_wind_speed_kmh: float = 60.0
    extreme_wind_speed_kmh: float = 90.0
    
    # Rain (mm per hour)
    heavy_rain_mm: float = 15.0
    extreme_rain_mm: float = 30.0
    
    # Temperature (C)
    high_temp_c: float = 38.0
    extreme_temp_c: float = 45.0
    low_temp_c: float = 0.0
    extreme_low_temp_c: float = -10.0
    
    # UV Index
    high_uv_index: float = 8.0
    extreme_uv_index: float = 11.0
    
    # Convective Activity / Storm Potential
    high_cape: float = 1500.0
    extreme_cape: float = 2500.0

    # Visibility (meters)
    low_visibility_m: float = 1000.0
    extreme_low_visibility_m: float = 200.0

    # Snowfall (mm water equivalent)
    heavy_snow_mm: float = 5.0
    extreme_snow_mm: float = 15.0

DEFAULT_THRESHOLDS = RiskThresholds()

# Scoring weights (max 100 per category)
def calculate_parameter_score(value: float, warning_thresh: float, critical_thresh: float) -> float:
    """Calculates a 0-100 score based on how far the value is past the thresholds."""
    if value < warning_thresh:
        # Scale 0 to 40
        if warning_thresh == 0: return 0.0
        return min(40.0, (value / warning_thresh) * 40.0)
    elif value < critical_thresh:
        # Scale 40 to 80
        diff = critical_thresh - warning_thresh
        if diff == 0: return 80.0
        return 40.0 + min(40.0, ((value - warning_thresh) / diff) * 40.0)
    else:
        # Scale 80 to 100
        # For critical, cap at 100
        over = value - critical_thresh
        return min(100.0, 80.0 + (over * 2.0))

def calculate_inverse_parameter_score(value: float, warning_thresh: float, critical_thresh: float) -> float:
    """Calculates score for parameters where lower is worse (like cold temp or visibility)."""
    if value > warning_thresh:
        return 0.0
    elif value > critical_thresh:
        diff = warning_thresh - critical_thresh
        if diff == 0: return 80.0
        return 40.0 + min(40.0, ((warning_thresh - value) / diff) * 40.0)
    else:
        over = critical_thresh - value
        return min(100.0, 80.0 + (over * 2.0))
