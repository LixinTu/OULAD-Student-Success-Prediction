-- Example mart-level query patterns for BI tools
SELECT *
FROM student_risk_daily
WHERE run_date = CURRENT_DATE
ORDER BY risk_score DESC
LIMIT 100;

SELECT run_date,
       code_module,
       student_count,
       avg_risk_score,
       high_risk_rate
FROM course_summary_daily
ORDER BY run_date DESC, high_risk_rate DESC;

SELECT *
FROM experiment_results
ORDER BY run_ts DESC, uplift_scenario;

SELECT *
FROM alert_log
ORDER BY run_ts DESC;
