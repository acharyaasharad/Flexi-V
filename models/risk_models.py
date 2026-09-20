from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class RiskSignal(BaseModel):
    parameter: str
    level: str # e.g., "WARNING", "CRITICAL", "INFO"
    message: str
    value: float
    threshold: float
    timestamp: Optional[str] = None
    severity_score: float = 0.0 # 0-100 score for this specific signal

class SourceCitation(BaseModel):
    title: str
    url: str
    snippet: str
    source_domain: str
    relevance_score: Optional[float] = None
    published_date: Optional[str] = None

class RiskAssessment(BaseModel):
    location_name: str
    overall_risk_level: str # "LOW", "MODERATE", "HIGH", "EXTREME"
    overall_risk_score: float = 0.0 # 0-100
    primary_risk: str = "None"
    peak_risk_window: Optional[str] = None
    confidence_score: float = 95.0
    signals: List[RiskSignal] = Field(default_factory=list)
    summary: str
    recommendations: List[str] = Field(default_factory=list)
    sources: List[SourceCitation] = Field(default_factory=list)
    hourly_risk_scores: List[float] = Field(default_factory=list)
    
    # Optional flags to indicate degraded mode
    is_deterministic_fallback: bool = False
