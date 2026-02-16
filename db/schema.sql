-- Core schemas for Route B separation
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS stg;
CREATE SCHEMA IF NOT EXISTS int;
CREATE SCHEMA IF NOT EXISTS mart;
CREATE SCHEMA IF NOT EXISTS ml;

-- Legacy compatibility tables in public schema
CREATE TABLE IF NOT EXISTS student_risk_daily (
    run_date DATE,
    id_student BIGINT,
    code_module VARCHAR(16),
    week INTEGER,
    risk_score DOUBLE PRECISION,
    high_risk_flag INTEGER,
    weekly_score_mean DOUBLE PRECISION,
    cum_submissions DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS course_summary_daily (
    run_date DATE,
    week INTEGER,
    code_module VARCHAR(16),
    student_count INTEGER,
    avg_risk_score DOUBLE PRECISION,
    high_risk_rate DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS experiment_results (
    run_ts TIMESTAMP,
    uplift_scenario DOUBLE PRECISION,
    control_rate DOUBLE PRECISION,
    treatment_rate DOUBLE PRECISION,
    rate_diff DOUBLE PRECISION,
    p_value DOUBLE PRECISION,
    ci_low DOUBLE PRECISION,
    ci_high DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS alert_log (
    run_ts TIMESTAMP,
    alert_type VARCHAR(64),
    high_risk_rate DOUBLE PRECISION,
    spike_pct DOUBLE PRECISION,
    message TEXT
);

-- New Route B model output table
CREATE TABLE IF NOT EXISTS ml.student_risk_scores (
    run_date TIMESTAMP,
    week INTEGER,
    id_student BIGINT,
    code_module VARCHAR(16),
    risk_score DOUBLE PRECISION,
    high_risk_flag INTEGER,
    model_version VARCHAR(64),
    model_backend VARCHAR(32),
    threshold DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
