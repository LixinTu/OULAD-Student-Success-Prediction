select 1
where (
    select count(distinct week)
    from {{ ref('mart_student_risk_weekly') }}
) <= 1
