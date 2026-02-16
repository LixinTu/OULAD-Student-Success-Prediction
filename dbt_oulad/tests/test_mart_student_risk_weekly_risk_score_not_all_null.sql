select 1
where not exists (
    select 1
    from {{ ref('mart_student_risk_weekly') }}
    where risk_score is not null
)
