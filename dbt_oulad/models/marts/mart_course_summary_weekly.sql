select
    run_date,
    week,
    code_module,
    count(distinct id_student) as students,
    avg(risk_score) as avg_risk_score,
    sum(high_risk_flag) as high_risk_students
from {{ ref('mart_student_risk_weekly') }}
group by 1, 2, 3
