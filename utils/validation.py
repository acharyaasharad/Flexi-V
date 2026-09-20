from typing import Any, Dict

def validate_location_query(query: str) -> bool:
    """Validates that a location query is non-empty and reasonable."""
    if not query or not isinstance(query, str):
        return False
    if len(query.strip()) < 2:
        return False
    return True

def sanitize_gemini_response(response_text: str) -> str:
    """Basic sanitization for LLM output."""
    if not response_text:
        return "No response provided."
    return response_text.strip()
