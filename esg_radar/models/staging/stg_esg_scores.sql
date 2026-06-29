-- Staging model: clean and standardize raw ESG scores
-- Source: esg_raw.esg_scores (loaded from Kaggle dataset)

with source as (
    select * from {{ source('esg_raw', 'esg_scores') }}
),

staged as (
    select
        -- identifiers
        ticker,
        name                            as company_name,
        industry,
        exchange,
        currency,

        -- raw scores
        environment_score,
        social_score,
        governance_score,
        total_score,

        -- normalized scores (0-100)
        environment_score_normalized,
        social_score_normalized,
        governance_score_normalized,
        total_score_normalized,

        -- grades
        environment_grade,
        social_grade,
        governance_grade,
        total_grade,

        -- levels
        environment_level,
        social_level,
        governance_level,
        total_level,

        -- derived fields
        esg_risk_label,
        strongest_pillar,
        weakest_pillar,
        industry_rank,
        industry_avg_score,
        above_industry_avg,

        -- numeric grades for sorting
        total_grade_numeric,
        environment_grade_numeric,
        social_grade_numeric,
        governance_grade_numeric,

        -- metadata
        last_processing_date,
        ingested_at,
        as_of_date

    from source
)

select * from staged
