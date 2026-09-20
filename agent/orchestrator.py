from models.agent_models import AgentContext, AgentResponse
from models.risk_models import RiskAssessment, RiskSignal
from risk.risk_engine import evaluate_weather_risk
from agent.weather_agent import get_weather_data
from agent.tavily_agent import gather_context
from agent.gemini_agent import synthesize_risk_report
from utils.logger import setup_logger

logger = setup_logger("orchestrator")

def process_query(query: str, user_mode: str = "General Public") -> AgentResponse:
    """
    Main orchestration logic:
    1. Fetch Location & Weather
    2. Evaluate Risk Rules
    3. Search Tavily conditionally
    4. Synthesize with Gemini
    """
    logger.info(f"Processing query: {query} with mode: {user_mode}")
    context = AgentContext(query=query)
    
    # 1. Weather & Location
    geo, forecast = get_weather_data(query)
    if not geo or not forecast:
        return AgentResponse(text="Could not find location or weather data for that query.")
        
    context.geocoding = geo
    context.weather_data = forecast
    
    # 2. Risk Engine
    signals, overall_score, hourly_scores, peak_window, primary_risk = evaluate_weather_risk(forecast)
    context.risk_signals = signals
    
    # Determine risk level based on score
    overall_level = "LOW"
    if overall_score >= 80: overall_level = "CRITICAL"
    elif overall_score >= 60: overall_level = "HIGH"
    elif overall_score >= 40: overall_level = "MODERATE"
    
    # 3. Web Research
    # Only search Tavily if risk is Moderate or higher to save credits and time
    if overall_score >= 40.0:
        signal_names = [s.parameter for s in signals] if signals else []
        try:
            research = gather_context(geo.name, signal_names)
            context.research_results = research
        except Exception as e:
            logger.error(f"Tavily search failed gracefully: {e}")
            context.research_results = []
    else:
        logger.info("Risk is LOW, skipping Tavily search.")
        context.research_results = []
    
    # Pack deterministic data into context for Gemini to see
    context.chat_history = [{"role": "system", "content": f"User Mode: {user_mode}\nDetermined Overall Risk Level: {overall_level}\nDetermined Risk Score: {overall_score}\nPeak Window: {peak_window}\nPrimary Risk: {primary_risk}\nHourly Scores: {hourly_scores}"}]

    # 4. Synthesize
    response = synthesize_risk_report(context)
    response.weather_data = forecast
    
    # Ensure structured risk has the deterministic values intact regardless of Gemini
    if response.structured_risk:
        response.structured_risk["overall_risk_score"] = overall_score
        response.structured_risk["hourly_risk_scores"] = hourly_scores
        response.structured_risk["peak_risk_window"] = peak_window
        response.structured_risk["primary_risk"] = primary_risk
        response.structured_risk["overall_risk_level"] = overall_level
        
    return response
