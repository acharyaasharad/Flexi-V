from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from models.weather_models import WeatherForecastResponse, GeocodingResult
from models.risk_models import RiskSignal, SourceCitation

class AgentContext(BaseModel):
    query: str
    geocoding: Optional[GeocodingResult] = None
    weather_data: Optional[WeatherForecastResponse] = None
    risk_signals: List[RiskSignal] = Field(default_factory=list)
    research_results: List[SourceCitation] = Field(default_factory=list)
    chat_history: List[Dict[str, str]] = Field(default_factory=list)
    
class AgentResponse(BaseModel):
    text: str
    structured_risk: Optional[Dict[str, Any]] = None # Will hold serialized RiskAssessment if generated
    weather_data: Optional[WeatherForecastResponse] = None # For plotting
