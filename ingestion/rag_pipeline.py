"""
ESG Radar — RAG Pipeline (LangChain 1.x compatible)
-----------------------------------------------------
Loads ESG data, creates embeddings, stores in ChromaDB,
and answers questions via LangChain + OpenAI.

Run:
    python ingestion/rag_pipeline.py
"""

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

CHROMA_DIR = "data/chroma_db"
DATA_PATH  = "data/processed/esg_clean_final.json"


# ── Load ESG data ─────────────────────────────────────────────────────────────
def load_esg_documents() -> list[Document]:
    log.info(f"Loading ESG data from {DATA_PATH}")

    with open(DATA_PATH) as f:
        records = [json.loads(line) for line in f]

    documents = []
    for r in records:
        text = f"""
Company: {r.get('name', '')} (Ticker: {r.get('ticker', '')})
Industry: {r.get('industry', '')}
Exchange: {r.get('exchange', '')}

ESG Scores (0-100 normalized):
- Total ESG Score: {r.get('total_score_normalized', 'N/A')}
- Environment Score: {r.get('environment_score_normalized', 'N/A')}
- Social Score: {r.get('social_score_normalized', 'N/A')}
- Governance Score: {r.get('governance_score_normalized', 'N/A')}

ESG Grades:
- Total Grade: {r.get('total_grade', 'N/A')} ({r.get('total_level', 'N/A')} level)
- Environment Grade: {r.get('environment_grade', 'N/A')}
- Social Grade: {r.get('social_grade', 'N/A')}
- Governance Grade: {r.get('governance_grade', 'N/A')}

ESG Risk Assessment:
- Risk Label: {r.get('esg_risk_label', 'N/A')}
- Strongest Pillar: {r.get('strongest_pillar', 'N/A')}
- Weakest Pillar: {r.get('weakest_pillar', 'N/A')}

Industry Context:
- Industry Rank: #{r.get('industry_rank', 'N/A')} in {r.get('industry', '')}
- Industry Average Score: {r.get('industry_avg_score', 'N/A')}
- Above Industry Average: {r.get('above_industry_avg', 'N/A')}

Last processed: {r.get('last_processing_date', 'N/A')}
        """.strip()

        documents.append(Document(
            page_content=text,
            metadata={
                "ticker":   r.get("ticker", ""),
                "name":     r.get("name", ""),
                "industry": r.get("industry", ""),
                "grade":    r.get("total_grade", ""),
                "risk":     r.get("esg_risk_label", ""),
            }
        ))

    log.info(f"Created {len(documents)} documents")
    return documents


# ── Build vector store ────────────────────────────────────────────────────────
def build_vectorstore(documents: list[Document]) -> Chroma:
    log.info("Building ChromaDB vector store...")

    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(documents)
    log.info(f"Split into {len(chunks)} chunks")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )

    log.info(f"Vector store built and saved to {CHROMA_DIR}")
    return vectorstore


# ── Load existing vector store ────────────────────────────────────────────────
def load_vectorstore() -> Chroma:
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )
    return Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings
    )


# ── Build RAG chain ───────────────────────────────────────────────────────────
def build_rag_chain(vectorstore: Chroma):
    llm = ChatOllama(
        model="llama3.2",
        temperature=0,
    )

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}
    )

    prompt = ChatPromptTemplate.from_template("""
You are an ESG analyst assistant. Use the following ESG data context to answer the question accurately and concisely.
If the answer is not in the context, say so clearly.

Context:
{context}

Question: {question}

Answer:""")

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain, retriever


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    Path(CHROMA_DIR).mkdir(parents=True, exist_ok=True)

    # Build or load vector store
    chroma_path = Path(CHROMA_DIR)
    if chroma_path.exists() and any(chroma_path.iterdir()):
        log.info("Loading existing vector store...")
        vectorstore = load_vectorstore()
    else:
        documents   = load_esg_documents()
        vectorstore = build_vectorstore(documents)

    chain, retriever = build_rag_chain(vectorstore)

    # Test queries
    questions = [
        "Which companies have the highest ESG scores overall?",
        "What are the best performing companies in the Technology industry for ESG?",
        "Which companies have the weakest governance scores?",
        "What industries have the most Low Risk ESG companies?",
        "Which energy companies perform above their industry average on ESG?",
    ]

    print("\n── ESG Radar RAG — Test Queries ─────────────────────────────")
    for q in questions:
        print(f"\nQ: {q}")
        answer = chain.invoke(q)
        print(f"A: {answer}")
        print("-" * 60)
