"""
ESG Radar — Airflow DAG
-------------------------
Orchestrates the full pipeline: ingest -> upload to GCS -> load to BigQuery -> run dbt

Schedule: daily at 6 AM UTC
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

PROJECT_ROOT = "/Users/macbookair/EPITA/esg-radar"

default_args = {
    "owner": "niveda",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="esg_radar_pipeline",
    default_args=default_args,
    description="End-to-end ESG data pipeline: ingest, store, transform",
    schedule="0 6 * * *",  # daily at 6 AM UTC
    start_date=datetime(2026, 6, 1),
    catchup=False,
    tags=["esg", "data-engineering"],
) as dag:

    # Task 1: Run ingestion script (clean CSV -> JSON)
    run_ingestion = BashOperator(
        task_id="run_ingestion",
        bash_command=f"cd {PROJECT_ROOT} && source venv/bin/activate && python ingestion/esg_ingestion.py",
    )

    # Task 2: Upload clean data to GCS
    upload_to_gcs = BashOperator(
        task_id="upload_to_gcs",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            "gsutil cp data/processed/esg_clean_final.json "
            "gs://esg-radar-raw-data-niveda/esg/esg_clean_final.json"
        ),
    )

    # Task 3: Load data into BigQuery
    load_to_bigquery = BashOperator(
        task_id="load_to_bigquery",
        bash_command=(
            "bq load --source_format=NEWLINE_DELIMITED_JSON --autodetect --replace "
            "esg-radar-niveda:esg_raw.esg_scores "
            "gs://esg-radar-raw-data-niveda/esg/esg_clean_final.json"
        ),
    )

    # Task 4: Run dbt models
    run_dbt = BashOperator(
        task_id="run_dbt",
        bash_command=(
            f"cd {PROJECT_ROOT}/esg_radar && "
            f"source {PROJECT_ROOT}/venv/bin/activate && "
            "dbt run"
        ),
    )

    # Task 5: Run dbt tests (data quality checks)
    test_dbt = BashOperator(
        task_id="test_dbt",
        bash_command=(
            f"cd {PROJECT_ROOT}/esg_radar && "
            f"source {PROJECT_ROOT}/venv/bin/activate && "
            "dbt test"
        ),
    )

    # Define task dependencies — the pipeline flow
    run_ingestion >> upload_to_gcs >> load_to_bigquery >> run_dbt >> test_dbt
