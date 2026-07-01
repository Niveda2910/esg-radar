"""
ESG Radar — Streamlit Dashboard + Chat Interface
-------------------------------------------------
Run:
    streamlit run streamlit/app.py
"""

import os
import sys
import json
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add project root to path for RAG imports
sys.path.append(str(Path(__file__).parent.parent / "ingestion"))

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ESG Radar",
    page_icon="��",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    """Load ESG data from processed JSON file."""
    data_path = Path(__file__).parent.parent / "data/processed/esg_clean_final.json"
    records = []
    with open(data_path) as f:
        for line in f:
            records.append(json.loads(line))
    return pd.DataFrame(records)

@st.cache_resource
def load_rag_chain():
    """Load RAG chain (cached so it only loads once)."""
    try:
        from rag_pipeline import load_vectorstore, build_rag_chain
        vectorstore      = load_vectorstore()
        chain, retriever = build_rag_chain(vectorstore)
        return chain
    except Exception as e:
        return None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://em-content.zobj.net/source/apple/354/seedling_1f331.png", width=60)
    st.title("ESG Radar")
    st.caption("EU Market Intelligence Platform")
    st.divider()

    page = st.radio(
        "Navigate",
        ["📊 Dashboard", "💬 ESG Chat"],
        label_visibility="collapsed"
    )

    st.divider()
    st.caption("Data: Kaggle ESG Dataset • 722 companies")
    st.caption("Pipeline: GCS → BigQuery → dbt → RAG")

# ── Load data ─────────────────────────────────────────────────────────────────
df = load_data()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "📊 Dashboard":
    st.title("🌱 ESG Radar Dashboard")
    st.caption("Powered by dbt + BigQuery + LangChain")

    # ── Filters ───────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        industries = ["All"] + sorted(df["industry"].dropna().unique().tolist())
        selected_industry = st.selectbox("Industry", industries)
    with col2:
        risk_labels = ["All"] + sorted(df["esg_risk_label"].dropna().unique().tolist())
        selected_risk = st.selectbox("ESG Risk Level", risk_labels)
    with col3:
        grades = ["All"] + sorted(df["total_grade"].dropna().unique().tolist(), reverse=True)
        selected_grade = st.selectbox("ESG Grade", grades)

    # Apply filters
    filtered = df.copy()
    if selected_industry != "All":
        filtered = filtered[filtered["industry"] == selected_industry]
    if selected_risk != "All":
        filtered = filtered[filtered["esg_risk_label"] == selected_risk]
    if selected_grade != "All":
        filtered = filtered[filtered["total_grade"] == selected_grade]

    # ── KPI metrics ───────────────────────────────────────────────────────────
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Companies", len(filtered))
    m2.metric("Avg ESG Score", f"{filtered['total_score_normalized'].mean():.1f}/100")
    m3.metric("Low Risk Companies", len(filtered[filtered["esg_risk_label"] == "Low Risk"]))
    m4.metric("Industries Covered", filtered["industry"].nunique())

    st.divider()

    # ── Row 1: Risk distribution + Industry avg ───────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("ESG Risk Distribution")
        risk_counts = filtered["esg_risk_label"].value_counts().reset_index()
        risk_counts.columns = ["Risk Level", "Count"]
        color_map = {
            "Low Risk": "#2ecc71",
            "Medium Risk": "#f39c12",
            "High Risk": "#e67e22",
            "Very High Risk": "#e74c3c"
        }
        fig = px.pie(
            risk_counts,
            values="Count",
            names="Risk Level",
            color="Risk Level",
            color_discrete_map=color_map,
            hole=0.4
        )
        fig.update_layout(margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Top 10 Industries by ESG Score")
        industry_avg = (
            filtered.groupby("industry")["total_score_normalized"]
            .mean()
            .sort_values(ascending=True)
            .tail(10)
            .reset_index()
        )
        industry_avg.columns = ["Industry", "Avg ESG Score"]
        fig2 = px.bar(
            industry_avg,
            x="Avg ESG Score",
            y="Industry",
            orientation="h",
            color="Avg ESG Score",
            color_continuous_scale="Greens"
        )
        fig2.update_layout(margin=dict(t=20, b=20), coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Row 2: Pillar scores + Top performers ─────────────────────────────────
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("ESG Pillar Comparison")
        pillar_data = pd.DataFrame({
            "Pillar": ["Environment", "Social", "Governance"],
            "Average Score": [
                filtered["environment_score_normalized"].mean(),
                filtered["social_score_normalized"].mean(),
                filtered["governance_score_normalized"].mean()
            ]
        })
        fig3 = px.bar(
            pillar_data,
            x="Pillar",
            y="Average Score",
            color="Pillar",
            color_discrete_sequence=["#27ae60", "#2980b9", "#8e44ad"]
        )
        fig3.update_layout(margin=dict(t=20, b=20), showlegend=False)
        fig3.update_yaxes(range=[0, 100])
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("Top 10 ESG Performers")
        top10 = (
            filtered.nlargest(10, "total_score_normalized")[
                ["name", "industry", "total_score_normalized", "total_grade", "esg_risk_label"]
            ]
            .rename(columns={
                "name": "Company",
                "industry": "Industry",
                "total_score_normalized": "ESG Score",
                "total_grade": "Grade",
                "esg_risk_label": "Risk"
            })
        )
        st.dataframe(top10, use_container_width=True, hide_index=True)

    # ── Row 3: Scatter plot ───────────────────────────────────────────────────
    st.subheader("Environment vs Governance Scores")
    fig4 = px.scatter(
        filtered,
        x="environment_score_normalized",
        y="governance_score_normalized",
        color="esg_risk_label",
        hover_name="name",
        hover_data=["industry", "total_grade"],
        color_discrete_map=color_map,
        labels={
            "environment_score_normalized": "Environment Score (0-100)",
            "governance_score_normalized": "Governance Score (0-100)",
            "esg_risk_label": "Risk Level"
        }
    )
    fig4.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig4, use_container_width=True)

    # ── Full data table ───────────────────────────────────────────────────────
    with st.expander("View Full Dataset"):
        st.dataframe(
            filtered[[
                "ticker", "name", "industry",
                "total_score_normalized", "environment_score_normalized",
                "social_score_normalized", "governance_score_normalized",
                "total_grade", "esg_risk_label"
            ]].rename(columns={
                "ticker": "Ticker",
                "name": "Company",
                "industry": "Industry",
                "total_score_normalized": "ESG Score",
                "environment_score_normalized": "Environment",
                "social_score_normalized": "Social",
                "governance_score_normalized": "Governance",
                "total_grade": "Grade",
                "esg_risk_label": "Risk"
            }),
            use_container_width=True,
            hide_index=True
        )

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2: ESG CHAT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💬 ESG Chat":
    st.title("💬 ESG Analyst Chat")
    st.caption("Ask questions about ESG data — powered by RAG + Llama 3.2")

    # Load RAG chain
    with st.spinner("Loading ESG knowledge base..."):
        chain = load_rag_chain()

    if chain is None:
        st.error("RAG pipeline could not be loaded. Make sure Ollama is running.")
        st.code("ollama serve", language="bash")
        st.stop()

    # Example questions
    st.subheader("Example questions to try:")
    examples = [
        "Which companies have the highest ESG scores overall?",
        "What are the best performing Technology companies for ESG?",
        "Which companies have the weakest governance scores?",
        "Which energy companies perform above their industry average?",
        "What is Microsoft's ESG profile?",
    ]
    cols = st.columns(len(examples))
    for i, example in enumerate(examples):
        if cols[i].button(example, key=f"ex_{i}", use_container_width=True):
            st.session_state["chat_input"] = example

    st.divider()

    # Chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    prompt = st.chat_input("Ask anything about ESG data...")

    # Handle example button clicks
    if "chat_input" in st.session_state and st.session_state["chat_input"]:
        prompt = st.session_state["chat_input"]
        st.session_state["chat_input"] = ""

    if prompt:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get RAG answer
        with st.chat_message("assistant"):
            with st.spinner("Analyzing ESG data..."):
                try:
                    answer = chain.invoke(prompt)
                    st.markdown(answer)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer
                    })
                except Exception as e:
                    err = f"Error: {str(e)}\n\nMake sure Ollama is running: `ollama serve`"
                    st.error(err)
