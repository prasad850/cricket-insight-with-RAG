import streamlit as st
import plotly.express as px
import re
from langchain_ollama import OllamaLLM

from reasoning_engine import (
    get_stats,
    get_tactical_report,
    get_fallback_stats,
    resolve_player_name,
)

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Cricket AI Analyst", page_icon="🤖", layout="wide")
st.title("🤖 AI Cricket Analyst")

# ---------------- MEMORY ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- DISPLAY HISTORY ----------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "fig" in msg:
            st.plotly_chart(msg["fig"], use_container_width=True)

# ---------------- INTENT DETECTION ----------------
def detect_intent(prompt):
    p = prompt.lower()

    if ("vs" in p or "against" in p):
        return "matchup"
    elif "how to play" in p or "strategy" in p:
        return "strategy"
    else:
        return "general"

# ---------------- PLAYER EXTRACTION ----------------
def extract_players(text):
    text = text.lower()
    text = re.sub(r"\bin (ipl|t20|odi|test)\b", "", text)

    if "vs" in text:
        parts = text.split("vs")
    elif "against" in text:
        parts = text.split("against")
    else:
        return None, None

    if len(parts) != 2:
        return None, None

    p1 = parts[0].replace("analyze", "").replace("analysis", "").strip()
    p2 = parts[1].replace("analysis", "").strip()

    # 🔥 remove extra words
    p1 = re.sub(r"[^a-zA-Z ]", "", p1)
    p2 = re.sub(r"[^a-zA-Z ]", "", p2)

    player1 = resolve_player_name(p1)
    player2 = resolve_player_name(p2)

    return player1, player2

# ---------------- LLM ANALYST ----------------
def run_llm(prompt, context=""):
    llm = OllamaLLM(model="mistral:latest")

    return llm.invoke(f"""
You are a professional cricket analyst.

RULES:
- Use given stats first
- Give practical strategy (shots + approach)
- Avoid generic answers

DATA:
{context if context else "No structured data"}

TASK:
1. Key insight
2. Strategy
3. Risk

User: {prompt}
""")

# ---------------- CHAT INPUT ----------------
if prompt := st.chat_input("Ask: 'Kohli vs Bumrah' or strategy questions..."):

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        intent = detect_intent(prompt)

        # ---------------- MATCHUP ----------------
        if intent == "matchup":

            batter, bowler = extract_players(prompt)

            if not batter or not bowler:
                response = "❌ Could not identify players. Try: 'Kohli vs Bumrah'"
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.stop()

            stats = get_stats(batter, bowler, "T20")

            fallback_used = False
            if not stats or stats.get("quality") == "low":
                stats = get_fallback_stats(batter, bowler, "T20")
                fallback_used = True

            if stats:
                report = get_tactical_report(stats)

                context = f"""
Batter: {batter}
Bowler: {bowler}
Runs: {stats.get('runs')}
Balls: {stats.get('balls')}
Strike Rate: {stats.get('strike_rate')}
Wickets: {stats.get('wickets')}
Dot%: {stats.get('dot_pct')}
Boundary%: {stats.get('boundary_pct')}
"""

                ai = run_llm(prompt, context)

                msg = f"### 🏏 {batter} vs {bowler}\n\n"

                if fallback_used:
                    msg += "_Using overall performance (low direct data)_\n\n"

                msg += f"**{report['title']}**\n{report['content']}\n\n"
                msg += f"🤖 {ai}"

                st.markdown(msg)

                # Chart
                fig = px.bar(
                    [
                        {"Metric": "Runs", "Value": stats["runs"]},
                        {"Metric": "Strike Rate", "Value": stats["strike_rate"]},
                        {"Metric": "Wickets", "Value": stats["wickets"]},
                        {"Metric": "Dot %", "Value": stats["dot_pct"]},
                    ],
                    x="Metric",
                    y="Value",
                    color="Metric",
                    title=f"{batter} vs {bowler} Analysis"
                )

                st.plotly_chart(fig, use_container_width=True)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": msg,
                    "fig": fig
                })

            else:
                ai = run_llm(prompt)
                st.markdown(ai)
                st.session_state.messages.append({"role": "assistant", "content": ai})

        # ---------------- STRATEGY ----------------
        elif intent == "strategy":
            ai = run_llm(prompt)
            st.markdown(ai)
            st.session_state.messages.append({"role": "assistant", "content": ai})

        # ---------------- GENERAL ----------------
        else:
            ai = run_llm(prompt)
            st.markdown(ai)
            st.session_state.messages.append({"role": "assistant", "content": ai})