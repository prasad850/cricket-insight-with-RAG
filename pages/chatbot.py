import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from langchain_ollama import OllamaLLM
from reasoning_engine import get_stats, get_tactical_report

st.set_page_config(page_title="Cricket AI Coach", page_icon="🤖", layout="wide")
st.title("🤖 AI Cricket Coach")
st.caption("Ask general strategy questions, or type: 'Analyze [Batter] vs [Bowler]' for a tactical breakdown.")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display History (including graphs)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "fig" in message:
            st.plotly_chart(message["fig"])

# Chat Input
if prompt := st.chat_input("Ask strategy or type: 'Analyze [Batter] vs [Bowler]'"):
    # Save user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # 1. DATA-DRIVEN ANALYSIS LOGIC
        if " vs " in prompt.lower():
            try:
                # Basic Parsing
                text = prompt.lower().replace("analyze", "").strip()
                names = text.split(" vs ")
                batter = names[0].strip().title()
                bowler = names[1].strip().title()
                
                # Fetch stats (Defaulting to T20 for chatbot analysis)
                stats = get_stats(batter, bowler, match_type="T20")
                
                if stats:
                    # Get Tactical Report
                    report = get_tactical_report(stats)
                    
                    # Display Strategy Report
                    st.markdown(f"### 🎯 Tactical Report: {batter} vs {bowler}")
                    if report['style'] == 'error': st.error(f"**{report['title']}**\n\n{report['content']}")
                    elif report['style'] == 'success': st.success(f"**{report['title']}**\n\n{report['content']}")
                    else: st.info(f"**{report['title']}**\n\n{report['content']}")
                    
                    # Display Metrics
                    st.write(f"- **Runs Scored:** {stats['runs']} | **Balls Faced:** {stats['balls']} | **Strike Rate:** {stats['strike_rate']:.2f} | **Dismissals:** {stats['wickets']}")
                    
                    # Generate Chart
                    balls_per_dismissal = stats['balls'] / max(1, stats['wickets'])
                    fig = go.Figure()
                    
                    fig.add_trace(go.Indicator(
                        mode="gauge+number",
                        value=stats['strike_rate'],
                        title={'text': "Strike Rate"},
                        domain={'x': [0, 0.45], 'y': [0, 1]},
                        gauge={
                            'axis': {'range': [0, 250]},
                            'bar': {'color': "#1f77b4"},
                            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 140}
                        }
                    ))
                    
                    fig.add_trace(go.Indicator(
                        mode="gauge+number",
                        value=balls_per_dismissal,
                        title={'text': "Balls per Dismissal"},
                        domain={'x': [0.55, 1], 'y': [0, 1]},
                        gauge={
                            'axis': {'range': [0, 50]},
                            'bar': {'color': "#2ca02c"},
                            'threshold': {'line': {'color': "darkgreen", 'width': 4}, 'thickness': 0.75, 'value': 20}
                        }
                    ))
                    
                    fig.update_layout(height=300, title_text=f"Performance: {batter} vs {bowler}", margin=dict(l=20, r=20, t=50, b=20))
                    st.plotly_chart(fig)
                    
                    # Save to session state
                    st.session_state.messages.append({"role": "assistant", "content": "Analysis completed.", "fig": fig})
                else:
                    msg = "I couldn't find stats for that matchup in the database."
                    st.markdown(msg)
                    st.session_state.messages.append({"role": "assistant", "content": msg})
                    
            except Exception as e:
                st.error("Format error: Please use 'Analyze [Batter] vs [Bowler]'")
        
        # 2. GENERAL AI COACH LOGIC (Using Mistral)
        else:
            with st.spinner("Thinking..."):
                llm = OllamaLLM(model="mistral:latest") 
                response = llm.invoke(f"You are an expert cricket coach. Answer this: {prompt}")
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})