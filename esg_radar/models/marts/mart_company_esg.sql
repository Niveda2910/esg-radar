-- Mart: Company-level ESG leaderboard
-- Used for: RAG layer + dashboard company cards

with staged as (
    select * from {{ ref('stg_esg_scores') }}
),

final as (
    select
        ticker,
        company_name,
        industry,
        exchange,

        -- scores
        total_score_normalized,
        environment_score_normalized,
        social_score_normalized,
        governance_score_normalized,

        -- grades
        total_grade,
        environment_grade,
        social_grade,
        governance_grade,

        -- risk
        esg_risk_label,
        strongest_pillar,
        weakest_pillar,

        -- industry context
        industry_rank,
        industry_avg_score,
        above_industry_avg,

        -- overall rank across all companies
        rank() over (
            order by total_score_normalized desc
        ) as overall_rank,

        -- rank within industry
        rank() over (
            partition by industry
            order by total_score_normalized desc
        ) as industry_rank_recalc,

        as_of_date

    from staged
)

select * from final
order by overall_rank
