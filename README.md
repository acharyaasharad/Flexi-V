# AI Weather Risk Alert Agent

A complete production-quality college project that acts as an intelligent weather-risk decision-support agent.

## Core Features
- **Live Weather Data**: Powered by Open-Meteo for accurate, deterministic weather metrics.
- **Risk Engine**: Deterministic Python rules evaluate weather data safely to identify risks (high winds, extreme temperatures, heavy rain, etc.).
- **Real-Time Web Research**: Uses Tavily API to fetch current external evidence, such as official disaster warnings or news.
- **Gemini Reasoning**: Integrates the `google-genai` SDK to synthesize weather data and external research, explaining risks and generating personalized recommendations.
- **Gradio Dashboard**: A full Gradio UI with interactive Plotly charts, data visualizations, and an intelligent chat interface.

## Setup Instructions

1. **Clone/Navigate to the repository**
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure environment**:
   - Copy `.env.example` to `.env`
   - Fill in your `GEMINI_API_KEY` and `TAVILY_API_KEY`
5. **Run the application**:
   ```bash
   python app.py
   ```
