import streamlit as st
import plotly.graph_objects as go
from langchain_ollama import OllamaLLM

from reasoning_engine import (
    get_all_teams,
    get_players_by_team,
    get_stats,
    get_tactical_report,
    get_all_seasons,
    get_fallback_stats
)

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Cricket Insight Engine", layout="wide")
st.title("🏏 Cricket Insight Engine (AI + Data)")

# ---------------- SIDEBAR ----------------
st.sidebar.header("Filter Settings")

m_type = st.sidebar.selectbox("Select Match Format", ["T20", "ODI", "IPL"])

available_seasons = ["All Time"] + get_all_seasons()
selected_season = st.sidebar.selectbox("Select Season", available_seasons)

teams = get_all_teams(m_type)

# ---------------- PLAYER SELECTION ----------------
col1, col2 = st.columns(2)

with col1:
    team_batter = st.selectbox("Select Batter Team", teams)
    batter = st.selectbox(
        "Select Batter",
        get_players_by_team(team_batter, m_type, role="batter", season=selected_season)
    )

with col2:
    team_bowler = st.selectbox("Select Bowler Team", teams)
    bowler = st.selectbox(
        "Select Bowler",
        get_players_by_team(team_bowler, m_type, role="bowler", season=selected_season)
    )

# ---------------- ANALYSIS ----------------
if st.button("Analyze Matchup"):

    if batter == bowler:
        st.error("Batter and Bowler cannot be the same!")
        st.stop()

    # -------- DIRECT MATCHUP --------
    stats = get_stats(batter, bowler, m_type)

    # -------- FALLBACK --------
    fallback_used = False
    if not stats or stats.get("quality") == "low":
        stats = get_fallback_stats(batter, bowler, m_type)
        fallback_used = True

    st.markdown("### 🎯 Tactical Strategy (AI + Data)")

    # -------- REPORT --------
    if stats:
        report = get_tactical_report(stats)

        if fallback_used:
            st.warning("⚠️ Limited direct data. Using overall player analysis.")

        if report['style'] == 'error':
            st.error(f"**{report['title']}**\n\n{report['content']}")
        elif report['style'] == 'success':
            st.success(f"**{report['title']}**\n\n{report['content']}")
        else:
            st.info(f"**{report['title']}**\n\n{report['content']}")

    else:
        st.warning("No database stats found. Using AI-only strategy.")

    # -------- AI ANALYST --------
    with st.spinner("Generating AI insights..."):
        try:
            llm = OllamaLLM(model="mistral:latest")

            db_context = ""
            if stats:
                db_context = f"""
Batter: {batter}
Bowler: {bowler}
Runs: {stats.get('runs', 0)}
Balls: {stats.get('balls', 0)}
Strike Rate: {stats.get('strike_rate', 0)}
Wickets: {stats.get('wickets', 0)}
Dot Percentage: {stats.get('dot_pct', 0)}
Boundary Percentage: {stats.get('boundary_pct', 0)}
"""

            ai_prompt = f"""
You are a professional cricket analyst.

RULES:
- Use given stats first
- Give practical strategy (shots + approach)
- Avoid generic answers

DATA:
{db_context if db_context else "No structured data"}

TASK:
1. Key insight
2. Strategy for batter
3. Strategy for bowler

Keep answer short (3-4 lines).
"""

            ai_response = llm.invoke(ai_prompt)

        except Exception:
            ai_response = "AI service unavailable. Showing data-based insights only."

    if ai_response:
        st.markdown("### 🤖 AI Analyst Insights")
        st.info(ai_response)

    # -------- METRICS --------
    if stats:
        st.write("---")
        st.subheader("📊 Performance Metrics")

        # 1. Clean row of metrics instead of giant gauge charts
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Runs Scored", stats.get('runs', 0))
        c2.metric("Strike Rate", stats.get('strike_rate', 0))
        c3.metric("Wickets", stats.get('wickets', 0))
        
        balls = stats.get('balls', 1)
        wkt = stats.get('wickets', 0)
        c4.metric("Balls/Dismissal", round(balls / wkt if wkt > 0 else balls, 1))

        # 2. Second row of tactical secondary metrics
        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Balls Faced", stats.get('balls', 0))
        c6.metric("Dot Ball %", f"{stats.get('dot_pct', 0)}%")
        c7.metric("Boundary %", f"{stats.get('boundary_pct', 0)}%")
        c8.metric("Data Depth", stats.get('quality', 'unknown').title())

        # 3. Simple modern Bar Chart 
        st.write(" ")
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["Runs", "Balls", "Dot %", "Boundary %", "Strike Rate"],
            y=[
                stats.get('runs', 0), 
                stats.get('balls', 0), 
                stats.get('dot_pct', 0), 
                stats.get('boundary_pct', 0), 
                stats.get('strike_rate', 0)
            ],
            marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
            texttemplate='%{y}',
            textposition='outside'
        ))
        fig.update_layout(
            title="Overview Comparison", 
            height=350, 
            margin=dict(t=40, b=0, l=0, r=0), 
            yaxis=dict(visible=False, showticklabels=False)
        )
        st.plotly_chart(fig, use_container_width=True)