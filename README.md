# OULAD Student Success Analytics Platform (Flagship v2)

🚀 A cloud-ready, production-style analytics platform that transforms exploratory notebook work into a modular, CI-validated, containerized student retention system.

This repository demonstrates:

- End-to-end ETL → Time-aware ML → SHAP explainability
- Postgres-backed BI marts
- Threshold & spike alerting
- Offline A/B experiment simulation
- ROI sensitivity modeling
- Dockerized execution + CI quality gates

The original exploratory notebook is preserved: `oulad-student-success-prediction.ipynb`.

---

## ⭐ What Makes This Different

Unlike typical ML portfolio projects, this repository:

- Separates exploration from production-grade code
- Implements time-based validation to prevent data leakage
- Publishes BI-ready database marts
- Includes alerting and experiment planning
- Enforces formatting, linting, and CI gates
- Supports containerized and cloud-ready deployment

---

## ⚡ 2-Minute Reviewer Overview

One command runs the full workflow:

ETL → Feature Engineering → Time-aware Model → SHAP → BI Marts → Alerts → A/B Simulation → ROI → Executive Summary

Demo mode ensures reproducibility even without raw OULAD data.

## Executive Overview
This repository presents a **production-style student retention analytics platform** built from the OULAD domain. It transforms exploratory notebook work into a modular pipeline with reproducible execution, database-backed marts, alerting, experimentation, and executive reporting.

> The original exploratory notebook is preserved: `oulad-student-success-prediction.ipynb`.

## Business Context (Student Retention)
Universities lose tuition revenue and student outcomes when at-risk learners are not identified early. This platform converts weekly behavior and assessment signals into:
- risk scoring for intervention teams,
- operational threshold/spike alerting,
- offline experiment planning support,
- ROI sensitivity analysis for budget decisions.

## Architecture Diagram
### Local / Container Runtime
```text
Raw OULAD CSVs (or Demo Generator)
          |
          v
      ETL Layer
          |
          v
 Feature Engineering (time-aware)
          |
          v
Model Train/Eval + SHAP Explain
          |
          v
Prediction + BI Marts + Alerts
          |
          v
A/B Simulation + ROI + Executive Report
          |
          v
Postgres (primary) / SQLite (fallback)
```

### Production AWS Reference Architecture
```text
[S3 Raw Zone] --> [ECS Scheduled Pipeline Task] --> [RDS Postgres Marts]
       |                    |                           |
       |                    v                           v
       |             [CloudWatch Logs/Alarms]     [Power BI Service]
       |
       +--> [S3 Artifacts: metrics, SHAP, reports]
```

## Data Pipeline Design
Entrypoint: `src/pipeline.py`
1. Extract OULAD data (`src/etl/extract.py`), with DEMO MODE fallback when raw files are missing.
2. Transform weekly student-level event data (`src/etl/transform.py`).
3. Load processed data and initialize DB schema (`src/etl/load.py`).
4. Build time-aware features (`src/features/build_features.py`).
5. Train risk model using week-based split (`src/model/train.py`).
6. Evaluate performance (`src/model/evaluate.py`).
7. Generate SHAP explainability artifacts (`src/model/explain.py`).
8. Publish marts (`src/marts/build_marts.py`).
9. Trigger alerts and log them (`src/alerts/alert.py`).
10. Run offline A/B simulation + ROI grid (`src/experiments/ab_simulation.py`).
11. Produce executive summary (`reports/executive_summary.md`).

## Time-Based ML Validation
To avoid random leakage, the model is evaluated with time ordering:
- Train: `week < SPLIT_WEEK`
- Test: `week >= SPLIT_WEEK`

This approximates real operations where future student behavior must be predicted from historical data.

## Explainability
- **sklearn backend**: SHAP artifacts are generated (`outputs/shap_top_features.json`, `outputs/shap_summary.png`).
- **pytorch/tensorflow backends**: permutation importance is generated and written to `outputs/shap_top_features.json` with the same JSON schema as sklearn.

## Alerting System
Implemented alerts:
- **Threshold alert**: high-risk share exceeds configurable threshold.
- **Spike alert**: week-over-week mean risk increase exceeds configured percentage.

Alerts are saved to `outputs/alerts/alert_latest.md` and inserted into `alert_log`.

## Experiment Framework
Offline experiment simulation on top-K at-risk students:
- seeded control/treatment assignment,
- uplift scenarios: **3%, 5%, 8%**,
- bootstrap confidence intervals,
- two-proportion z-test,
- persisted experiment rows in `experiment_results`.

## ROI Modeling
ROI sensitivity grid is generated via:

`ROI = incremental_passes * value_per_pass - intervention_cost`

Output: `reports/roi_sensitivity.csv`.

## Validation
Recommended local quality gates:
```bash
python -m compileall src
ruff check src tests
black --check src tests
pytest -q
python -m src.pipeline --demo
```

These same checks are wired into `.github/workflows/daily_pipeline.yml`.

## Assumptions & Limitations
- A/B results are **offline simulation**, not causal proof from live experimentation.
- Uplift scenarios (3%, 5%, 8%) are planning assumptions.
- Synthetic demo mode is for reproducibility and CI, not for production decisions.
- Model and feature definitions are intentionally lightweight for portfolio demonstration.

## Outputs (Key Files)
### Core metrics & predictions
- `outputs/metrics_latest.json`
- `outputs/predictions_latest.csv` (runtime output; not tracked)
- `outputs/shap_top_features.json`

### Marts (BI-ready samples)
- `outputs/marts/student_risk_daily_sample.csv`
- `outputs/marts/course_summary_daily_sample.csv`
- `outputs/marts/student_risk_latest.csv`
- `outputs/marts/course_summary_latest.csv`

### Alerts, experiments, and reports
- `outputs/alerts/alert_latest.md`
- `outputs/experiments/assignment_latest.csv`
- `reports/ab_test_report.md`
- `reports/roi_sensitivity.csv`
- `reports/executive_summary.md`

## Cloud Deployment Plan
- **Storage** abstraction in `src/storage.py`: `LocalStorage` + real `S3Storage` (boto3).
- **Database**: Postgres by `DATABASE_URL`, SQLite fallback for local portability.
- **Compute**: Dockerized app service (`docker/Dockerfile`, `docker-compose.yml`).
- **Observability**: structured logs ready for CloudWatch-style ingestion.
- **BI layer**: marts aligned for Power BI connectivity.

## How to Run
### Postgres-backed demo flow (recommended)
1) Start Postgres:
```bash
docker compose up -d postgres
```

2) Install dependencies:
```bash
pip install -r requirements.txt
```

3) Point the pipeline to Postgres (pipeline falls back to SQLite only when `DATABASE_URL` is unset):
```bash
export DATABASE_URL=postgresql://oulad:oulad@localhost:5432/oulad_analytics
```

4) Run the full demo pipeline and publish marts:
```bash
make run
```

5) Verify tables and row counts:
```bash
make verify-postgres
```

### Local SQLite fallback
If `DATABASE_URL` is not set, the same `make run` command writes to local SQLite at `data/processed/pipeline.db`.

### Optional Deep Learning Backends (PyTorch / TensorFlow)
Sklearn remains the default baseline. PyTorch/TensorFlow are optional and only used when `MODEL_BACKEND` is set explicitly.

```bash
# PyTorch backend
pip install -r requirements-pt.txt
MODEL_BACKEND=pytorch python -m src.pipeline --demo

# TensorFlow backend
pip install -r requirements-tf.txt
MODEL_BACKEND=tensorflow python -m src.pipeline --demo
```

PyTorch installation may vary by OS/CUDA; if needed, use the official PyTorch install command for your platform.

### Optional environment variables
- `DATABASE_URL`
- `PIPELINE_DEMO_MODE=true|false`
- `SPLIT_WEEK=7`
- `HIGH_RISK_THRESHOLD=0.25`
- `RISK_SPIKE_THRESHOLD_PCT=0.10`
- `MODEL_BACKEND=sklearn|pytorch|tensorflow`
- `STORAGE_BACKEND=local|s3`
- `AWS_REGION=us-east-1`
- `S3_BUCKET=<your-bucket>`
- `S3_PREFIX=oulad-artifacts`

## Power BI: Connect to Postgres
1) In Power BI Desktop, select **Get Data** → **PostgreSQL database**.
2) Server: `localhost`.
3) Database: `oulad_analytics`.
4) Credentials: username `oulad`, password `oulad`.
5) Choose **Import** mode for quickest demo setup.
6) Select these tables:
   - `student_risk_daily`
   - `course_summary_daily`
   - `experiment_results`
   - `alert_log`
7) Click **Load** and build visuals (examples: risk trend by `run_date`, module heatmap by `high_risk_rate`, alert timeline by `run_ts`).

### S3 Artifact Publishing
Set these env vars: `STORAGE_BACKEND`, `AWS_REGION`, `S3_BUCKET`, `S3_PREFIX`.

When `STORAGE_BACKEND=s3`, the pipeline uploads only small/stable artifacts:
- `outputs/metrics_latest.json`
- `outputs/shap_top_features.json`
- `outputs/marts/*.csv`
- `outputs/alerts/*.md`
- `reports/*.md`
- `reports/*.csv`
- `outputs/artifacts_manifest.json`

The manifest acts as run audit evidence (`run_id`, timestamp, model backend, db mode, file sizes, and storage URIs).

Example:
```bash
export STORAGE_BACKEND=s3
export AWS_REGION=us-east-1
export S3_BUCKET=my-oulad-artifacts
export S3_PREFIX=prod
python -m src.pipeline --demo
```

> AWS credentials are intentionally not stored in this repo. Use IAM roles, AWS SSO, or a local AWS profile.

## CI/CD
GitHub Actions (`.github/workflows/daily_pipeline.yml`) runs on push, nightly schedule, and manual dispatch. It performs compile/lint/test checks and runs the demo pipeline before uploading artifacts.

## Project Structure
```text
src/
  config.py
  storage.py
  pipeline.py
  utils/logging.py
  etl/{extract.py,transform.py,load.py}
  features/build_features.py
  model/{train.py,predict.py,evaluate.py,explain.py}
  marts/build_marts.py
  alerts/alert.py
  experiments/ab_simulation.py

db/{schema.sql,marts.sql}
docker/Dockerfile
docker-compose.yml
.github/workflows/daily_pipeline.yml
tests/test_pipeline_smoke.py
Makefile
```

## Future Improvements
- Replace offline simulation with live randomized intervention experiments.
- Add model drift monitoring, retraining cadence, and model registry.
- Extend security controls (RLS/IAM) and data contracts for enterprise rollout.
