import json
from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL
from models.agent_models import AgentContext, AgentResponse
from models.alert_models import RiskAssessment
from utils.logger import setup_logger

logger = setup_logger("gemini_agent")

def synthesize_risk_report(context: AgentContext) -> AgentResponse:
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not found.")
        return AgentResponse(text="Error: Gemini API key is not configured.", structured_risk=None)

    logger.info(f"Synthesizing report using {GEMINI_MODEL}...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # We ask Gemini to generate JSON matching the RiskAssessment schema
    system_instruction = (
        "You are an expert AI weather risk analyst. "
        "Analyze the provided weather data, detected risk signals, and recent news/research. "
        "Synthesize a clear, accurate, and professional risk assessment. "
        "DO NOT invent weather values. Only use the provided factual data. "
        "Produce your response as valid JSON matching this schema: "
        "{'location_name': str, 'overall_risk_level': 'LOW'|'MODERATE'|'HIGH'|'EXTREME', "
        "'summary': str, 'recommendations': list[str]}."
    )
    
    # Build prompt context
    context_str = f"Query: {context.query}\n"
    if context.geocoding:
        context_str += f"Location: {context.geocoding.name}, {context.geocoding.admin1}, {context.geocoding.country}\n"
    
    context_str += f"Signals Detected: {[s.model_dump() for s in context.risk_signals]}\n"
    if context.research_results:
        context_str += f"Recent News/Research: {[s.model_dump() for s in context.research_results]}\n"

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=context_str,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
            ),
        )
        
        # Clean the response text from potential markdown wrappers
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # Parse the JSON
        parsed_json = json.loads(text)
        
        # Ensure it has signals and sources from our determinisic engines
        parsed_json["signals"] = [s.model_dump() for s in context.risk_signals]
        parsed_json["sources"] = [s.model_dump() for s in context.research_results]
        
        return AgentResponse(text="Analysis complete.", structured_risk=parsed_json)
        
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return AgentResponse(text=f"Error generating analysis: {e}", structured_risk=None)

def chat_with_gemini(chat_history: list, new_message: str, current_assessment: dict) -> str:
    """Handles follow-up questions using Gemini Interactions API logic."""
    if not GEMINI_API_KEY:
        return "Error: Gemini API key is not configured."

    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # We construct a history for the chat model
    system_prompt = (
        "You are an expert AI weather risk assistant. Answer the user's questions based on the "
        "following current risk assessment context. Do not invent new weather data.\n\n"
        f"Context:\n{json.dumps(current_assessment, indent=2) if current_assessment else 'No active context.'}"
    )
    
    contents = []
    # GenAI Python SDK expects a list of Content objects or dicts
    # However, since we are doing a simple conversational turn, we can build it manually.
    for msg in chat_history:
        role = 'user' if msg['role'] == 'user' else 'model'
        contents.append(
            genai.types.Content(role=role, parts=[genai.types.Part.from_text(msg['content'])])
        )
    
    contents.append(
        genai.types.Content(role='user', parts=[genai.types.Part.from_text(new_message)])
    )
    
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )
        return response.text
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return "Sorry, I encountered an error answering your question."
