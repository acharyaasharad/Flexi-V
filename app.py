import gradio as gr
import plotly.graph_objects as go
from agent.orchestrator import process_query
from utils.formatting import format_risk_assessment_markdown
import json
import pandas as pd
import os
from datetime import datetime

# Ensure data dir exists
os.makedirs("data", exist_ok=True)
HISTORY_FILE = "data/alert_history.json"

def save_to_history(location, assessment):
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except:
            pass
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "location": location,
        "level": assessment.get("overall_risk_level", "UNKNOWN"),
        "score": assessment.get("overall_risk_score", 0.0),
        "primary_risk": assessment.get("primary_risk", "None")
    }
    history.insert(0, entry)
    history = history[:20] # Keep last 20
    
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return pd.DataFrame(columns=["Timestamp", "Location", "Risk Level", "Score", "Primary Risk"])
    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
        return pd.DataFrame([{
            "Timestamp": d["timestamp"][:16].replace("T", " "),
            "Location": d["location"],
            "Risk Level": d["level"],
            "Score": d["score"],
            "Primary Risk": d["primary_risk"]
        } for d in data])
    except:
        return pd.DataFrame(columns=["Timestamp", "Location", "Risk Level", "Score", "Primary Risk"])

def create_weather_charts(forecast, risk_scores=None):
    """Generates Plotly charts for the UI based on forecast data and deterministic risk scores."""
    if not forecast or not forecast.hourly:
        return go.Figure(), go.Figure(), go.Figure()
        
    df = pd.DataFrame({
        "time": pd.to_datetime(forecast.hourly.time),
        "temperature": forecast.hourly.temperature_2m,
        "wind_speed": forecast.hourly.wind_speed_10m,
        "precipitation": forecast.hourly.precipitation
    })
    
    # Limit to next 48 hours
    limit = min(48, len(df))
    df = df.head(limit)
    
    # 1. Temp and Wind Chart
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df['time'], y=df['temperature'], mode='lines', name='Temp (°C)', line=dict(color='orange')))
    fig1.add_trace(go.Scatter(x=df['time'], y=df['wind_speed'], mode='lines', name='Wind (km/h)', yaxis='y2', line=dict(color='teal', dash='dot')))
    fig1.update_layout(
        title="Temperature & Wind Speed",
        yaxis=dict(title="Temperature (°C)", title_font=dict(color="orange"), tickfont=dict(color="orange")),
        yaxis2=dict(title="Wind Speed (km/h)", title_font=dict(color="teal"), tickfont=dict(color="teal"), overlaying="y", side="right"),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    # 2. Precipitation Chart
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=df['time'], y=df['precipitation'], name='Rain (mm)', marker_color='blue'))
    fig2.update_layout(
        title="Precipitation",
        yaxis=dict(title="Rain (mm)"),
        margin=dict(l=20, r=20, t=40, b=20)
    )

    # 3. Hourly Risk Score Chart
    fig3 = go.Figure()
    if risk_scores and len(risk_scores) >= limit:
        fig3.add_trace(go.Scatter(x=df['time'], y=risk_scores[:limit], fill='tozeroy', mode='lines', name='Risk Score', line=dict(color='red')))
        fig3.update_layout(
            title="Hourly Risk Severity (0-100)",
            yaxis=dict(title="Risk Score", range=[0, 100]),
            margin=dict(l=20, r=20, t=40, b=20)
        )
    
    return fig1, fig2, fig3

def analyze_location(location: str):
    """Gradio handler for analyzing a location."""
    try:
        if not location.strip():
            empty_fig = go.Figure()
            return "Please enter a valid location.", empty_fig, empty_fig, empty_fig, None
            
        response = process_query(location, "General Public")
        
        if not response.structured_risk:
            empty_fig = go.Figure()
            empty_fig.update_layout(title="No data available")
            return response.text, empty_fig, empty_fig, empty_fig, None
            
        assessment = response.structured_risk
        
        markdown_output = format_risk_assessment_markdown(assessment)
        
        # Save to history
        save_to_history(location, assessment)
        
        # Generate Charts
        hourly_risk = assessment.get("hourly_risk_scores", [])
        chart1, chart2, chart3 = create_weather_charts(response.weather_data, hourly_risk)
        
        return markdown_output, chart1, chart2, chart3, assessment
    except Exception as e:
        import traceback
        # Never show traceback to end user
        error_msg = f"> [!CRITICAL]\n> **An internal system error occurred during analysis.** Please try again."
        empty_fig = go.Figure()
        return error_msg, empty_fig, empty_fig, empty_fig, None

def refresh_history():
    return load_history()

# Build Gradio App
with gr.Blocks(title="AI Weather Risk Alert Agent", theme=gr.themes.Soft()) as app:
    # State component to hold the current risk assessment
    current_assessment = gr.State()
    
    gr.Markdown("# 🌤️ AI Weather Risk Alert Agent")
    gr.Markdown("Real-time deterministic weather risk analysis powered by fallback-resilient AI synthesis.")
    
    with gr.Row():
        location_input = gr.Textbox(label="Location", placeholder="Enter city or region...", scale=3)
        analyze_btn = gr.Button("Analyze Risk", variant="primary", scale=1)
        
    with gr.Tabs():
        with gr.TabItem("📊 Dashboard"):
            assessment_output = gr.Markdown("### Risk Assessment will appear here...")
            
        with gr.TabItem("📈 Forecast & Risk"):
            gr.Markdown("### Deterministic Hourly Analysis")
            chart_risk = gr.Plot(label="Hourly Risk Score")
            with gr.Row():
                chart_temp = gr.Plot(label="Temperature & Wind")
                chart_precip = gr.Plot(label="Precipitation")
                
        with gr.TabItem("🕰️ Alert History"):
            history_btn = gr.Button("Refresh History")
            history_table = gr.Dataframe(value=load_history())
            history_btn.click(fn=refresh_history, outputs=[history_table])

    # Wiring Main Analysis
    analyze_btn.click(
        fn=analyze_location,
        inputs=[location_input],
        outputs=[assessment_output, chart_temp, chart_precip, chart_risk, current_assessment]
    ).then(
        fn=refresh_history,
        outputs=[history_table]
    )

    location_input.submit(
        fn=analyze_location,
        inputs=[location_input],
        outputs=[assessment_output, chart_temp, chart_precip, chart_risk, current_assessment]
    ).then(
        fn=refresh_history,
        outputs=[history_table]
    )
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 7860))
    app.launch(server_name="0.0.0.0", server_port=port)
