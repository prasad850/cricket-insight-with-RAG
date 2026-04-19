import streamlit as st
from reasoning_engine import get_all_teams, get_players_by_team, get_matchup_stats
from langchain_ollama import OllamaLLM

st.set_page_config(page_title="Cricket Insight Engine")
st.title("🏏 Cricket Insight Engine (2026)")

# --- 1. Selection Layer (2026 Season Only) ---
col1, col2 = st.columns(2)
with col1:
    team_batter = st.selectbox("Select Batter Team", get_all_teams())
    batter = st.selectbox("Select Batter", get_players_by_team(team_batter))
with col2:
    team_bowler = st.selectbox("Select Bowler Team", get_all_teams())
    bowler = st.selectbox("Select Bowler", get_players_by_team(team_bowler))

# --- 2. Analytics Layer ---
if st.button("Get Analysis"):
    stats = get_matchup_stats(batter, bowler)
    
    if stats:
        st.write(f"### Historical Analysis: {batter} vs {bowler}")
        st.metric("Runs", stats['runs'])
        st.metric("Dismissals", stats['dismissals'])
        
        # --- 3. Reasoning Layer ---
        llm = OllamaLLM(model="mistral:latest")
        prompt = f"""
        Analyze this cricket matchup: 
        Batter: {batter}, Bowler: {bowler}. 
        Historical Stats: {stats['runs']} runs in {stats['balls']} balls, Dismissals: {stats['dismissals']}.
        
        Provide a tactical coach's recommendation. 
        Note: The current match venue is Wankhede Stadium. Adjust advice based on this pitch context.
        """
        
        with st.spinner("AI Coach is analyzing..."):
            analysis = llm.invoke(prompt)
            st.info(analysis)
    else:
        st.warning("No historical matchup data found for these players.")