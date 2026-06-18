# app.py

import streamlit as st
import requests

import os
API_BASE = os.getenv("API_BASE", "http://localhost:8000")


st.set_page_config(
    page_title="Nifty 50 Financial Insights",
    page_icon="📈",
    layout="wide"
)

# ── Sidebar Navigation ──────────────────────────────────────────────
st.sidebar.title("📈 Financial Insights")
page = st.sidebar.radio("Navigate", ["Pipeline Dashboard", "Chat Assistant", "Activity Logs"])

st.sidebar.markdown("---")
st.sidebar.caption("Nifty 50 Agentic AI System")
st.sidebar.caption("Databricks + Google ADK + ChromaDB RAG")


# ══════════════════════════════════════════════════════════════════
# PAGE 1 — Pipeline Dashboard
# ══════════════════════════════════════════════════════════════════
if page == "Pipeline Dashboard":
    st.title("Financial Insights Pipeline")
    st.markdown("Run the full multi-agent pipeline: **Ingestion → Processing → Analytics**")

    task = st.text_area(
        "What would you like the pipeline to analyze?",
        value="Validate the data, analyze IT sector performance over all years, and generate a 2024 insights report.",
        height=100
    )

    if st.button("🚀 Run Pipeline", type="primary"):
        with st.spinner("Running multi-agent pipeline... this may take 30-60 seconds"):
            try:
                response = requests.post(
                    f"{API_BASE}/pipeline/run",
                    json={"task": task},
                    timeout=180
                )
                if response.status_code == 200:
                    data = response.json()
                    st.success("Pipeline completed successfully!")
                    st.markdown("### Results")
                    st.markdown(data["result"])
                else:
                    st.error(f"Error: {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to API. Make sure `python api.py` is running.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    st.markdown("---")
    st.markdown("### Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Data Validation Only"):
            with st.spinner("Validating data..."):
                response = requests.post(
                    f"{API_BASE}/agents/ingestion",
                    json={"task": "Validate all ingested Nifty 50 data and give a summary report"},
                    timeout=60
                )
                if response.status_code == 200:
                    st.info(response.json()["result"])

    with col2:
        if st.button("📈 Sector Comparison"):
            with st.spinner("Analyzing sectors..."):
                response = requests.post(
                    f"{API_BASE}/agents/processing",
                    json={"task": "Compare IT and Financials sectors performance"},
                    timeout=60
                )
                if response.status_code == 200:
                    st.info(response.json()["result"])

    with col3:
        if st.button("📋 2024 Full Report"):
            with st.spinner("Generating report..."):
                response = requests.post(
                    f"{API_BASE}/agents/analytics",
                    json={"task": "Generate a full financial insights report for 2024"},
                    timeout=60
                )
                if response.status_code == 200:
                    st.info(response.json()["result"])


# ══════════════════════════════════════════════════════════════════
# PAGE 2 — Chat Assistant (RAG)
# ══════════════════════════════════════════════════════════════════
elif page == "Chat Assistant":
    st.title("💬 Ask About Nifty 50 Stocks")
    st.markdown("Powered by RAG (ChromaDB) — ask anything about stocks, sectors, or anomalies (1998-2026)")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about any Nifty 50 stock, sector, or trend..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching financial data..."):
                try:
                    response = requests.post(
                        f"{API_BASE}/chat",
                        json={"question": prompt, "session_id": "streamlit_session"},
                        timeout=60
                    )
                    if response.status_code == 200:
                        answer = response.json()["answer"]
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        st.error(f"Error: {response.text}")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to API. Make sure `python api.py` is running.")

    if st.session_state.messages:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()


# ══════════════════════════════════════════════════════════════════
# PAGE 3 — Activity Logs
# ══════════════════════════════════════════════════════════════════
elif page == "Activity Logs":
    st.title("📋 Agent Activity Logs")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Recent Agent Runs")
        if st.button("🔄 Refresh Logs"):
            st.rerun()

        try:
            response = requests.get(f"{API_BASE}/logs/recent?limit=15")
            if response.status_code == 200:
                logs = response.json()["logs"]
                for log in logs:
                    status_icon = "✅" if log["status"] == "success" else "❌"
                    st.markdown(f"{status_icon} **{log['agent_name']}** — {log['message'][:80]}")
                    st.caption(f"Model: {log.get('model', 'N/A')} | ~{log.get('est_tokens', 0)} tokens | {log['timestamp']}")
                    st.markdown("---")
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to API.")

    with col2:
        st.subheader("Today's Token Usage")
        try:
            response = requests.get(f"{API_BASE}/logs/usage")
            if response.status_code == 200:
                usage = response.json()
                for model, stats in usage.items():
                    st.metric(
                        label=model,
                        value=f"{stats['total_tokens_today']:,} tokens",
                        delta=f"{stats['calls_today']} calls today"
                    )
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to API.")