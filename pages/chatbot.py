import streamlit as st
import plotly.express as px
from langchain_ollama import OllamaLLM
from reasoning_engine import get_stats, get_tactical_report

st.set_page_config(page_title="Cricket AI Coach", page_icon="🤖", layout="wide")
st.title("🤖 AI Cricket Coach")
st.caption("Ask general cricket strategy, or type 'Analyze [Batter] vs [Bowler]' for a tactical report.")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "fig" in message:
            st.plotly_chart(message["fig"])

# Chat Input
if prompt := st.chat_input("Ask about strategy or type: 'Analyze [Batter] vs [Bowler]'"):
    # Save user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # 1. MATCHUP ANALYSIS LOGIC
        if "analyze" in prompt.lower() and " vs " in prompt.lower():
            try:
                # Basic parsing to extract names from the prompt
                text = prompt.lower().replace("analyze", "").strip()
                names = text.split(" vs ")
                batter = names[0].strip().title()
                bowler = names[1].strip().title()
                
                # Fetch stats (Global stats for weakness/strength analysis)
                stats = get_stats(batter, bowler, match_type=None)
                
                if stats:
                    # Get Tactical Report (Weakness/Strength Logic)
                    report = get_tactical_report(stats)
                    
                    # Display Strategy Report with dynamic UI
                    st.markdown(f"### Tactical Report: {batter} vs {bowler}")
                    
                    if report['type'] == 'danger': st.error(f"**{report['status']}**: {report['message']}")
                    elif report['type'] == 'success': st.success(f"**{report['status']}**: {report['message']}")
                    else: st.info(f"**{report['status']}**: {report['message']}")
                    
                    # Display Metrics
                    st.write(f"- **Runs Scored:** {stats['runs']} | **Dismissals:** {stats['wickets']}")
                    
                    # Generate Chart
                    chart_data = {"Metric": ["Runs Scored", "Dismissals"], "Value": [stats['runs'], stats['wickets']]}
                    fig = px.bar(chart_data, x="Metric", y="Value", color="Metric", title=f"Matchup Stats: {batter} vs {bowler}")
                    st.plotly_chart(fig)
                    
                    # Save to session state
                    st.session_state.messages.append({"role": "assistant", "content": "Analysis completed.", "fig": fig})
                else:
                    msg = "I couldn't find stats for that matchup in the database."
                    st.markdown(msg)
                    st.session_state.messages.append({"role": "assistant", "content": msg})
                    
            except Exception as e:
                st.error("Format error: Please use 'Analyze [Batter] vs [Bowler]'")
        
        # 2. GENERAL AI COACH LOGIC
        else:
            with st.spinner("Thinking..."):
                llm = OllamaLLM(model="mistral:Latest")
                response = llm.invoke(f"You are an expert cricket coach. Answer this: {prompt}")
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})