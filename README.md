# 🌱 ESG Radar — End-to-End ESG Intelligence Platform

> An automated data pipeline and AI-powered analytics platform for ESG (Environmental, Social & Governance) intelligence across 722 public companies.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![dbt](https://img.shields.io/badge/dbt-1.11-orange)
![Airflow](https://img.shields.io/badge/Airflow-3.2-green)
![BigQuery](https://img.shields.io/badge/BigQuery-GCP-blue)
![LangChain](https://img.shields.io/badge/LangChain-1.3-purple)
![Streamlit](https://img.shields.io/badge/Streamlit-1.58-red)

---

## 📌 What This Project Solves

ESG analysts today manually collect sustainability reports from hundreds of company websites, copy scores into spreadsheets, and rebuild reports every quarter from scratch. This is slow, error-prone, and unscalable.

**ESG Radar automates this entire workflow:**
- Ingests and normalizes ESG data for 722 public companies
- Transforms raw scores into business-ready analytics using dbt
- Orchestrates the full pipeline daily with Airflow
- Lets analysts ask questions in plain English via a RAG-powered chat interface

---

## 🏗️ Architecture

```
Raw CSV Data
     │
     ▼
┌─────────────────┐
│  Python Ingestor │  ← Normalize, clean, enrich scores
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   GCS Bucket    │  ← Data lake (raw JSON)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    BigQuery     │  ← Cloud data warehouse
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   dbt Models    │  ← Staging + Mart transformations
│  stg_esg_scores │
│  mart_company   │
│  mart_industry  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Airflow DAG    │  ← Daily orchestration (6 AM UTC)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│         AI Layer                │
│  Embeddings: all-MiniLM-L6-v2  │
│  Vector Store: ChromaDB         │
│  LLM: Llama 3.2 (local)        │
│  Framework: LangChain           │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────┐
│    Streamlit    │  ← Dashboard + Chat interface
└─────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Data Ingestion | Python (pandas, requests) |
| Data Lake | Google Cloud Storage |
| Data Warehouse | Google BigQuery |
| Transformation | dbt (staging + mart models) |
| Orchestration | Apache Airflow 3.x |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector Store | ChromaDB |
| LLM | Llama 3.2 via Ollama (local, free) |
| RAG Framework | LangChain 1.x |
| Dashboard | Streamlit + Plotly |
| Cloud | GCP (BigQuery + GCS) |
| Version Control | Git + GitHub |

---

## 📊 What Gets Built

### dbt Models
- **`stg_esg_scores`** — Staging view: cleans and standardizes raw BigQuery table
- **`mart_company_esg`** — Company leaderboard with overall rank, industry rank, pillar scores
- **`mart_industry_esg`** — Industry aggregations: avg ESG score, risk distribution, peer benchmarks

### Streamlit App
- **Dashboard tab** — Interactive charts: risk distribution, industry rankings, pillar comparisons, scatter plots, top 10 performers, full filterable data table
- **Chat tab** — RAG-powered Q&A: ask questions about ESG data in plain English, answered by Llama 3.2 with context retrieved from ChromaDB

### Airflow DAG (`esg_radar_pipeline`)
Five tasks running daily at 6 AM UTC:
```
run_ingestion → upload_to_gcs → load_to_bigquery → run_dbt → test_dbt
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12
- GCP account with BigQuery and GCS enabled
- [Ollama](https://ollama.com) installed with `llama3.2` model

### 1. Clone the repo
```bash
git clone https://github.com/Niveda2910/esg-radar.git
cd esg-radar
```

### 2. Set up virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment variables
```bash
cp .env.example .env
# Edit .env and add your GCP project ID and credentials path
```

### 4. Run the ingestion pipeline
```bash
python ingestion/esg_ingestion.py
```

### 5. Set up dbt and run models
```bash
cd esg_radar
dbt run
dbt test
cd ..
```

### 6. Build the RAG vector store
```bash
# Make sure Ollama is running
ollama serve &
python ingestion/rag_pipeline.py
```

### 7. Launch the Streamlit app
```bash
python -m streamlit run streamlit/app.py
```

Open `http://localhost:8501` in your browser.

---

## 📁 Project Structure

```
esg-radar/
├── ingestion/
│   ├── esg_ingestion.py      ← Data cleaning & normalization
│   └── rag_pipeline.py       ← RAG pipeline (embeddings + LangChain)
├── esg_radar/
│   └── models/
│       ├── staging/
│       │   ├── stg_esg_scores.sql
│       │   └── sources.yml
│       └── marts/
│           ├── mart_company_esg.sql
│           └── mart_industry_esg.sql
├── airflow/
│   └── dags/
│       └── esg_pipeline_dag.py
├── streamlit/
│   └── app.py
├── data/
│   ├── raw/                  ← Raw source files (gitignored)
│   └── processed/            ← Cleaned JSON (gitignored)
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 💡 Key Engineering Decisions

**Why dbt?**
dbt enforces modularity and testability in SQL transformations. Staging models isolate raw data concerns; mart models serve business logic. This mirrors production analytics engineering workflows.

**Why local LLM (Llama 3.2)?**
Choosing a local model over OpenAI demonstrates understanding of cost/privacy trade-offs in production AI systems — a real consideration for enterprise ESG data which can be sensitive.

**Why ChromaDB?**
Lightweight vector store with no infrastructure overhead, suitable for local development and portfolio demonstration. In production this would swap to Pinecone or Weaviate.

**Why Airflow 3.x?**
Latest major version with significant scheduler improvements. Navigating breaking changes between Airflow 2.x and 3.x (CLI changes, DAG parameter renames) demonstrates hands-on troubleshooting ability.

---

## 📈 Sample Insights From The Data

- Only **3.2%** of 722 companies qualify as Low ESG Risk
- **Utilities** sector leads with avg ESG score of 63.1/100
- **Microsoft (MSFT)** scores 99.68/100 — highest in the dataset
- **Environment** is consistently the strongest pillar; **Governance** the weakest
- **32%** of companies are classified as Very High Risk — showing ESG maturity is still low across markets

---

## 🔮 Future Improvements

- [ ] Add real-time data ingestion via financial APIs
- [ ] Expand to European company data (EURONEXT, XETRA)
- [ ] Add dbt tests for data quality checks
- [ ] Deploy Streamlit app to GCP Cloud Run
- [ ] Add time-series tracking to monitor ESG score changes over time
- [ ] Fine-tune LLM on ESG-specific terminology

---

## 👩‍💻 Author

**Niveda Nadarassin**
Junior Data Engineer 
🔗 [GitHub](https://github.com/Niveda2910)

---

## 📄 License

MIT License — feel free to use this project as inspiration for your own portfolio.
