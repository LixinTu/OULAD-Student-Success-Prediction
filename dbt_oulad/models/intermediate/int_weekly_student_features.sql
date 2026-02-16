with base as (
    select
        sa.id_student,
        si.code_module,
        ((coalesce(sa.date_submitted, a.assessment_date, 0)) / 7)::integer as week,
        sa.score,
        sa.submitted
    from {{ ref('stg_student_assessment') }} sa
    left join {{ ref('stg_assessments') }} a
        on sa.id_assessment = a.id_assessment
    left join {{ ref('stg_student_info') }} si
        on sa.id_student = si.id_student
),
weekly as (
    select
        id_student,
        code_module,
        week,
        avg(score) as weekly_score_mean,
        sum(coalesce(submitted, 1)) as weekly_submissions
    from base
    group by 1, 2, 3
),
final as (
    select
        id_student,
        code_module,
        week,
        weekly_score_mean,
        weekly_submissions,
        sum(weekly_submissions) over (
            partition by id_student, code_module
            order by week
            rows between unbounded preceding and current row
        ) as cumulative_submissions,
        avg(weekly_score_mean) over (
            partition by id_student, code_module
            order by week
            rows between 2 preceding and current row
        ) as rolling_3_week_mean,
        weekly_score_mean
            - lag(weekly_score_mean) over (
                partition by id_student, code_module
                order by week
            ) as weekly_score_trend
    from weekly
)
select * from final
