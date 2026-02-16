# Route B Industrialization Plan (Discovery-First)

## Step 0 Discovery Findings

Repository scan command used:

```bash
rg -n "risk_score|high_risk|student_risk|alert_log|course_summary|experiment_results|CREATE TABLE|to_sql|copy_expert|insert into|write_|load_" src db tests README.md Makefile
```

### A) Current risk-score storage tables (name + schema)

1. **`student_risk_daily`** (currently unqualified, therefore `public.student_risk_daily` in Postgres):
   - Defined in `db/schema.sql`.
   - Written from `src/marts/build_marts.py::build_marts` via `db.insert_df("student_risk_daily", student_risk_daily)`.

2. **File output used by tests/docs**:
   - `outputs/marts/student_risk_daily_sample.csv` written in `src/marts/build_marts.py::build_marts`.

### B) Current risk-score columns observed

From `db/schema.sql` + `src/marts/build_marts.py`:

- `run_date`
- `id_student`
- `code_module`
- `week`
- `risk_score`
- `high_risk_flag`
- `weekly_score_mean`
- `cum_submissions`

### C) Where course summaries / alerts / experiments are written

1. **Course summary**:
   - Table: `course_summary_daily` (`public.course_summary_daily` in Postgres).
   - Built and inserted in `src/marts/build_marts.py::build_marts`.
   - CSV: `outputs/marts/course_summary_daily_sample.csv`.

2. **Alerts**:
   - Table: `alert_log` (`public.alert_log`).
   - Insert SQL in `src/alerts/alert.py::generate_alert`.
   - Markdown artifact: `outputs/alerts/alert_latest.md`.

3. **Experiment rows**:
   - Table: `experiment_results` (`public.experiment_results`).
   - Written in `src/experiments/ab_simulation.py::run_ab_simulation` with `db.insert_df("experiment_results", experiment_rows)`.
   - CSV/report artifacts: `outputs/experiments/assignment_latest.csv`, `reports/ab_test_report.md`, `reports/roi_sensitivity.csv`.

### D) Compatibility notes for migration to Route B

- Keep existing writes to legacy `public.student_risk_daily`, `public.course_summary_daily`, `public.alert_log`, and `public.experiment_results` to avoid breaking current consumers.
- Add schema-separated writes in parallel:
  - `ml.student_risk_scores` for model scoring history.
  - dbt-managed marts in `mart.*`.
- Do **not** infer legacy table names; discovery above is source of truth for compatibility.
- `DATABASE_URL` behavior should remain strict: when set, Postgres must be used and connection errors should fail loudly.
