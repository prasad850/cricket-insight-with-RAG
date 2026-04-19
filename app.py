import streamlit as st
from reasoning_engine import get_matchup_stats
from langchain_ollama import OllamaLLM

st.title("🏏 Cricket Insight Engine")

# 1. Inputs
batter = st.text_input("Enter Batter Name")
bowler = st.text_input("Enter Bowler Name")

if st.button("Get Analysis"):
    # 2. Get Data
    context_data = get_matchup_stats(batter, bowler)
    st.write(f"Data Found: {context_data}")
    
    # 3. Analyze with Llama 3
    if "No matchup data" not in context_data:
        llm = OllamaLLM(model="mistral:latest")
        prompt = f"As a cricket coach, analyze this matchup: {context_data}. Is this a good matchup for the batter or the bowler?"
        
        with st.spinner("Analyzing..."):
            analysis = llm.invoke(prompt)
            st.success(analysis)
    else:
        st.warning("Not enough data to analyze.")