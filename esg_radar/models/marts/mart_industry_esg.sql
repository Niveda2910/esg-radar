-- Mart: ESG performance aggregated by industry
-- Used for: dashboard industry comparison charts

with staged as (
    select * from {{ ref('stg_esg_scores') }}
),

industry_stats as (
    select
        industry,
        count(*)                                    as company_count,
        round(avg(total_score_normalized), 2)       as avg_esg_score,
        round(avg(environment_score_normalized), 2) as avg_environment_score,
        round(avg(social_score_normalized), 2)      as avg_social_score,
        round(avg(governance_score_normalized), 2)  as avg_governance_score,
        round(min(total_score_normalized), 2)       as min_esg_score,
        round(max(total_score_normalized), 2)       as max_esg_score,
        countif(esg_risk_label = 'Low Risk')        as low_risk_count,
        countif(esg_risk_label = 'Medium Risk')     as medium_risk_count,
        countif(esg_risk_label = 'High Risk')       as high_risk_count,
        countif(esg_risk_label = 'Very High Risk')  as very_high_risk_count,
        countif(above_industry_avg = true)          as above_avg_count
    from staged
    group by industry
)

select
    *,
    round(low_risk_count / company_count * 100, 1)       as pct_low_risk,
    round(above_avg_count / company_count * 100, 1)      as pct_above_avg
from industry_stats
order by avg_esg_score desc
