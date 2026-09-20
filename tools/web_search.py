import logging
from typing import List
from tavily import TavilyClient
from config import TAVILY_API_KEY
from models.risk_models import SourceCitation
from utils.source_validator import process_tavily_results
from utils.logger import setup_logger

logger = setup_logger("web_search_tool")

def search_weather_context(location_name: str, signals: List[str] = None) -> List[SourceCitation]:
    """
    Searches the web for recent contextual info regarding the weather at a location.
    Particularly useful if we detected risk signals and want to find official alerts.
    """
    if not TAVILY_API_KEY:
        logger.warning("No TAVILY_API_KEY, skipping web search.")
        return []

    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)
        
        # Build query
        signal_str = " ".join(signals) if signals else "weather warnings"
        query = f"{location_name} {signal_str} official news alert today"
        
        logger.info(f"Searching Tavily for query: '{query}'")
        
        # Use advanced search to get snippet content and ensure current data
        response = client.search(
            query=query,
            search_depth="advanced",
            time_range="d", # Past day
            max_results=5
        )
        
        results = response.get("results", [])
        return process_tavily_results(results)
        
    except Exception as e:
        logger.error(f"Error during Tavily search: {str(e)}")
        return []
