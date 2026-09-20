from models.risk_models import RiskAssessment

def format_risk_assessment_markdown(assessment: dict) -> str:
    """Formats the structured risk assessment dictionary into a markdown string for UI."""
    # Handle the fact that assessment might be a dict now (from Gemini response)
    
    # Use defaults if keys are missing
    loc_name = assessment.get("location_name", "Unknown Location")
    overall_level = assessment.get("overall_risk_level", "UNKNOWN")
    overall_score = assessment.get("overall_risk_score", 0.0)
    primary_risk = assessment.get("primary_risk", "None")
    peak_window = assessment.get("peak_risk_window", "Unknown")
    confidence = assessment.get("confidence_score", 0.0)
    summary = assessment.get("summary", "")
    is_fallback = assessment.get("is_deterministic_fallback", False)
    
    md = f"## 🌍 Risk Assessment for {loc_name}\n\n"
    
    if is_fallback:
        md += "> [!WARNING]\n> **AI SYNTHESIS TEMPORARILY UNAVAILABLE.** This is a deterministic report based strictly on weather rules.\n\n"
        
    # Risk Level Badge
    risk_emoji = {"LOW": "🟢", "MODERATE": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}.get(overall_level.upper(), "⚪")
    
    md += f"**Overall Risk Level:** {risk_emoji} {overall_level.upper()} (Score: {overall_score}/100)\n\n"
    md += f"**Primary Threat:** {primary_risk}\n\n"
    md += f"**Peak Risk Window:** {peak_window}\n\n"
    md += f"**Confidence Score:** {confidence}/100\n\n"
    
    # Summary
    md += f"### 📋 Summary\n{summary}\n\n"
    
    # Signals
    signals = assessment.get("signals", [])
    if signals:
        md += "### ⚠️ Risk Signals\n"
        for sig in signals:
            level = sig.get("level", "INFO")
            param = sig.get("parameter", "").replace('_', ' ').title()
            msg = sig.get("message", "")
            val = sig.get("value", 0.0)
            score = sig.get("severity_score", 0.0)
            level_emoji = {"WARNING": "🟡", "CRITICAL": "🔴", "INFO": "🔵"}.get(level, "▪️")
            md += f"- {level_emoji} **{param}**: {msg} (Value: {val} | Severity: {score:.1f}/100)\n"
        md += "\n"
        
    # Recommendations
    recs = assessment.get("recommendations", [])
    if recs:
        md += "### 🛡️ Recommendations\n"
        for rec in recs:
            md += f"- {rec}\n"
        md += "\n"
        
    # Sources
    sources = assessment.get("sources", [])
    if sources:
        md += "### 🔗 External Context & Sources\n"
        for src in sources:
            title = src.get("title", "Link")
            url = src.get("url", "#")
            domain = src.get("source_domain", "Source")
            md += f"- [{title}]({url}) - _{domain}_\n"
            
    return md
