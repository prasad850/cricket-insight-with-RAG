import streamlit as st
import plotly.express as px
from reasoning_engine import get_all_teams, get_players_by_team, get_stats, determine_strategy

# Page Configuration
st.set_page_config(page_title="Cricket Insight Engine", layout="wide")
st.title("🏏 Cricket Insight Engine (2026 Analysis)")

# --- 1. Selection Layer (2026 Season Context) ---
st.sidebar.header("Filter 2026 Squads")

# Fetch Data for Dropdowns
teams = get_all_teams()
format_choice = st.sidebar.selectbox("Select Match Format", ["T20", "ODI"])

col1, col2 = st.columns(2)
with col1:
    st.subheader("Batter Selection")
    team_batter = st.selectbox("Select Batter Team", teams, key="team1")
    batter = st.selectbox("Select Batter", get_players_by_team(team_batter, season="2026"))

with col2:
    st.subheader("Bowler Selection")
    team_bowler = st.selectbox("Select Bowler Team", teams, key="team2")
    bowler = st.selectbox("Select Bowler", get_players_by_team(team_bowler, season="2026"))

# --- 2. Analytics Layer ---
if st.button("Analyze Matchup"):
    if batter == bowler:
        st.error("Batter and Bowler cannot be the same person!")
    else:
        # Fetch Stats
        format_stats = get_stats(batter, bowler, match_type=format_choice)
        global_stats = get_stats(batter, bowler, match_type=None) # Global for weakness
        
        if format_stats:
            # A. Strategy Box
            strategy = determine_strategy(global_stats)
            st.success(f"### 🧠 Coach's Strategy\n{strategy}")
            
            # B. Metrics Display
            c1, c2, c3 = st.columns(3)
            c1.metric("Format Runs", format_stats['runs'])
            c2.metric("Strike Rate", format_stats['strike_rate'])
            c3.metric("Total Dismissals (Global)", global_stats['wickets'])
            
            # C. Interactive Graph (Plotly)
            st.write("---")
            st.subheader("Statistical Performance Visualization")
            chart_data = {
                "Metric": ["Global Runs", "Format Specific Runs"],
                "Value": [global_stats['runs'], format_stats['runs']]
            }
            fig = px.bar(chart_data, x="Metric", y="Value", color="Metric", 
                         title=f"Performance Overview: {batter} vs {bowler}")
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("No historical matchup data found for these players.")