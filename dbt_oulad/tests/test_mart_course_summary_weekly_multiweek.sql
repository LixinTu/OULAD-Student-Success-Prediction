select 1
where (
    select count(distinct week)
    from {{ ref('mart_course_summary_weekly') }}
) <= 1
