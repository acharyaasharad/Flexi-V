from typing import List
from models.risk_models import SourceCitation
from tools.web_search import search_weather_context

def gather_context(location_name: str, signals: List[str] = None) -> List[SourceCitation]:
    """Agentic wrapper to gather external research context."""
    return search_weather_context(location_name, signals)
