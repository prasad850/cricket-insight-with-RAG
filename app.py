import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from langchain_ollama import OllamaLLM
from reasoning_engine import get_all_teams, get_players_by_team, get_stats, get_tactical_report, get_all_seasons

# Page Setup
st.set_page_config(page_title="Cricket Analytics Dashboard", layout="wide")
st.title("🏏 Cricket Insight Engine (2026)")

# --- 1. Filter Section ---
st.sidebar.header("Filter Settings")
# Selecting format first dictates the teams and players available
m_type = st.sidebar.selectbox("Select Match Format", ["T20", "ODI", "IPL"])

# Option to choose year/season but stats remain overall
available_seasons = ["All Time"] + get_all_seasons()
selected_season = st.sidebar.selectbox("Select Season", available_seasons)

# Get teams based on the selected match_type
teams = get_all_teams(m_type)

col1, col2 = st.columns(2)
with col1:
    team_batter = st.selectbox("Select Batter Team", teams, key="t1")
    # Get players based on team, format, role, and season
    batter = st.selectbox("Select Batter", get_players_by_team(team_batter, m_type, role="batter", season=selected_season))

with col2:
    team_bowler = st.selectbox("Select Bowler Team", teams, key="t2")
    # Get players based on team, format, role, and season
    bowler = st.selectbox("Select Bowler", get_players_by_team(team_bowler, m_type, role="bowler", season=selected_season))

# --- 2. Analytics Section ---
if st.button("Analyze Matchup"):
    if batter == bowler:
        st.error("Batter and Bowler cannot be the same person!")
    else:
        # Fetch Stats (Filtered by format)
        stats = get_stats(batter, bowler, match_type=m_type)
        
        if stats:
            # A. Tactical Strategy Display
            st.markdown("### 🎯 Tactical Strategy (Mistral AI)")
            with st.spinner(f"Analyzing {batter} vs {bowler} using Mistral..."):
                try:
                    llm = OllamaLLM(model="mistral:latest")
                    prompt = f"Act as an expert cricket coach. Give a 2-sentence tactical strategy for the batter {batter} facing the bowler {bowler} in {m_type} cricket. The batter has scored {stats['runs']} runs off {stats['balls']} balls against this bowler, with {stats['wickets']} dismissals and a strike rate of {stats['strike_rate']:.2f}. Be actionable, insightful, and concise."
                    ai_response = llm.invoke(prompt)
                    st.success(f"**AI Strategy:**\n\n{ai_response}")
                except Exception as e:
                    # Fallback to static report if ollama fails
                    report = get_tactical_report(stats)
                    if report['style'] == 'error': st.error(f"**{report['title']}**\n\n{report['content']}")
                    elif report['style'] == 'success': st.success(f"**{report['title']}**\n\n{report['content']}")
                    else: st.info(f"**{report['title']}**\n\n{report['content']}")
                    st.warning(f"Could not reach Mistral AI. Displaying static strategy instead.")
            
            # B. Metrics
            st.write("---")
            st.subheader(f"Performance Analysis: {m_type}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Runs", stats['runs'])
            c2.metric("Strike Rate", f"{stats['strike_rate']:.2f}")
            c3.metric("Dismissals", stats['wickets'])
            
            # C. Visuals
            g1, g2 = st.columns(2)
            
            # Strike Rate Gauge
            fig1 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=stats['strike_rate'],
                title={'text': "Strike Rate"},
                gauge={
                    'axis': {'range': [0, 250]},
                    'bar': {'color': "#1f77b4"},
                    'steps': [
                        {'range': [0, 100], 'color': "#e0e0e0"},
                        {'range': [100, 150], 'color': "#b3cde3"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75, 'value': 140
                    }
                }
            ))
            fig1.update_layout(height=250, margin=dict(l=10, r=10, t=40, b=10))
            g1.plotly_chart(fig1, use_container_width=True)
            
            # Balls per Dismissal Gauge
            balls_per_dismissal = stats['balls'] / max(1, stats['wickets'])
            fig2 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=balls_per_dismissal,
                title={'text': "Balls per Dismissal"},
                gauge={
                    'axis': {'range': [0, 50]},
                    'bar': {'color': "#2ca02c"},
                    'steps': [
                        {'range': [0, 15], 'color': "#f2dede"},
                        {'range': [15, 30], 'color': "#dff0d8"}
                    ],
                    'threshold': {
                        'line': {'color': "darkgreen", 'width': 4},
                        'thickness': 0.75, 'value': 20
                    }
                }
            ))
            fig2.update_layout(height=250, margin=dict(l=10, r=10, t=40, b=10))
            g2.plotly_chart(fig2, use_container_width=True)
            
        else:
            st.warning(f"No matchup data found for these players in {m_type}.")