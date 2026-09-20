from typing import List, Dict, Any
from urllib.parse import urlparse
from config import PRIORITIZED_SOURCES
from models.risk_models import SourceCitation

def extract_domain(url: str) -> str:
    """Extracts the domain from a given URL."""
    try:
        domain = urlparse(url).netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return "unknown"

def process_tavily_results(results: List[Dict[str, Any]]) -> List[SourceCitation]:
    """
    Processes raw Tavily results into SourceCitation models.
    Optionally scores or sorts them based on PRIORITIZED_SOURCES.
    """
    citations = []
    for res in results:
        url = res.get("url", "")
        domain = extract_domain(url)
        
        # Determine relevance boost based on prioritized sources
        relevance_score = res.get("score", 0.5)
        for p_source in PRIORITIZED_SOURCES:
            if p_source in domain:
                relevance_score += 0.5 # Boost priority sources
                break
                
        citation = SourceCitation(
            title=res.get("title", "Untitled"),
            url=url,
            snippet=res.get("content", "")[:300] + "...", # truncate snippet
            source_domain=domain,
            relevance_score=relevance_score,
            published_date=res.get("published_date")
        )
        citations.append(citation)
        
    # Sort by relevance
    citations.sort(key=lambda x: x.relevance_score or 0, reverse=True)
    return citations
