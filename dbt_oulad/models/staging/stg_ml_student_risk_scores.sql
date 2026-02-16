select
    cast(run_date as timestamp) as run_date,
    cast(week as integer) as week,
    cast(id_student as bigint) as id_student,
    cast(code_module as varchar(16)) as code_module,
    cast(risk_score as double precision) as risk_score,
    cast(high_risk_flag as integer) as high_risk_flag,
    cast(model_version as varchar(64)) as model_version,
    cast(model_backend as varchar(32)) as model_backend,
    cast(threshold as double precision) as threshold,
    cast(created_at as timestamp) as created_at
from {{ source('ml', 'student_risk_scores') }}
