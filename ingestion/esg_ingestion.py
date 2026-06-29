"""
ESG Radar — Ingestion Script (Kaggle ESG Dataset)
--------------------------------------------------
Reads the raw ESG ratings CSV, normalizes it, enriches it
with derived fields, and saves a clean JSON to data/processed/.

Run:
    python ingestion/esg_ingestion.py
"""

import json
import logging
import pandas as pd
from datetime import date, datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

RAW_PATH   = Path("data/raw/esg_ratings_source.csv")
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SCORE_RANGES = {
    "environment_score": (200, 719),
    "social_score":      (160, 667),
    "governance_score":  (75,  475),
    "total_score":       (600, 1536),
}

def normalize_score(value, min_val, max_val):
    if pd.isna(value):
        return None
    return round((value - min_val) / (max_val - min_val) * 100, 2)

def grade_to_numeric(grade):
    mapping = {"AAA": 7, "AA": 6, "A": 5, "BBB": 4, "BB": 3, "B": 2, "CCC": 1}
    return mapping.get(str(grade).strip().upper(), 0)

def esg_risk_label(score):
    if score is None:
        return "Unknown"
    if score >= 75:
        return "Low Risk"
    elif score >= 50:
        return "Medium Risk"
    elif score >= 25:
        return "High Risk"
    else:
        return "Very High Risk"

def run():
    log.info(f"Reading raw data from {RAW_PATH}")
    df = pd.read_csv(RAW_PATH)
    log.info(f"Loaded {len(df)} records")

    df.columns = df.columns.str.strip().str.lower()
    df = df.drop(columns=["logo", "weburl", "cik"], errors="ignore")
    df["ticker"]   = df["ticker"].str.upper().str.strip()
    df["name"]     = df["name"].str.strip()
    df["industry"] = df["industry"].str.strip()
    df["exchange"] = df["exchange"].str.strip().str.replace('"', '')
    df["last_processing_date"] = pd.to_datetime(
        df["last_processing_date"], format="%d-%m-%Y", errors="coerce"
    ).dt.date.astype(str)

    for col, (mn, mx) in SCORE_RANGES.items():
        df[f"{col}_normalized"] = df[col].apply(lambda v: normalize_score(v, mn, mx))

    df["total_grade_numeric"]       = df["total_grade"].apply(grade_to_numeric)
    df["environment_grade_numeric"] = df["environment_grade"].apply(grade_to_numeric)
    df["social_grade_numeric"]      = df["social_grade"].apply(grade_to_numeric)
    df["governance_grade_numeric"]  = df["governance_grade"].apply(grade_to_numeric)
    df["esg_risk_label"]            = df["total_score_normalized"].apply(esg_risk_label)

    df["strongest_pillar"] = df[[
        "environment_score_normalized",
        "social_score_normalized",
        "governance_score_normalized"
    ]].idxmax(axis=1).str.replace("_score_normalized", "").str.capitalize()

    df["weakest_pillar"] = df[[
        "environment_score_normalized",
        "social_score_normalized",
        "governance_score_normalized"
    ]].idxmin(axis=1).str.replace("_score_normalized", "").str.capitalize()

    df["industry_rank"]      = df.groupby("industry")["total_score"].rank(ascending=False, method="min").astype("Int64")
    df["industry_avg_score"] = df.groupby("industry")["total_score_normalized"].transform("mean").round(2)
    df["above_industry_avg"] = df["total_score_normalized"] > df["industry_avg_score"]
    df["ingested_at"]        = datetime.utcnow().isoformat()
    df["as_of_date"]         = date.today().isoformat()

    today    = date.today().isoformat()
    out_path = OUTPUT_DIR / f"esg_clean_{today}.json"
    records  = df.to_dict(orient="records")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2, default=str)

    log.info(f"Saved {len(records)} clean records → {out_path}")

    print("\n── Dataset Summary ──────────────────────────────────────────")
    print(f"Total companies : {len(df)}")
    print(f"Industries      : {df['industry'].nunique()}")
    print(f"\nESG Risk Distribution:")
    print(df["esg_risk_label"].value_counts().to_string())
    print(f"\nTop 10 ESG Performers:")
    print(df.nlargest(10, "total_score_normalized")[
        ["ticker", "name", "industry", "total_score_normalized", "total_grade"]
    ].to_string(index=False))

    return records

if __name__ == "__main__":
    run()
