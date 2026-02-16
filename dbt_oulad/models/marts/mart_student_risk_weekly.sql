select
    ml.run_date,
    ml.week,
    ml.id_student,
    ml.code_module,
    ml.risk_score,
    ml.high_risk_flag,
    feat.weekly_score_mean,
    feat.weekly_submissions,
    feat.cumulative_submissions,
    feat.rolling_3_week_mean,
    feat.weekly_score_trend,
    si.studied_credits,
    si.age_band_num,
    si.imd_band_num,
    si.disability_flag,
    si.pass_probability_base,
    ml.model_version,
    ml.model_backend,
    ml.threshold,
    ml.created_at
from {{ ref('stg_ml_student_risk_scores') }} ml
left join {{ ref('int_weekly_student_features') }} feat
    on ml.id_student = feat.id_student
    and ml.code_module = feat.code_module
    and ml.week = feat.week
left join {{ ref('stg_student_info') }} si
    on ml.id_student = si.id_student
    and ml.code_module = si.code_module
