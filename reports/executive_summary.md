# Executive Summary

## Business Problem
Student attrition creates academic and financial risk. This pipeline operationalizes weekly risk detection and intervention planning using behavioral signals.

## Architecture
Automated ETL -> feature engineering -> time-aware ML -> explainability -> marts -> alerting -> experiment simulation -> ROI.

## Model Performance
- AUC: **0.992**
- PR AUC: **0.994**
- Precision@0.5: **0.971**
- Recall@0.5: **0.947**

## Alerts Triggered
See `outputs/alerts/alert_latest.md` for threshold and spike checks.

## Experiment Outcomes
See `reports/ab_test_report.md` for uplift scenarios (3%, 5%, 8%) with CIs and z-test p-values.

## ROI Findings
Top ROI scenario: uplift=10%, cost=50.0, roi=3500.00.

## Production Roadmap
1. Deploy scheduler + model retraining cadence.
2. Add drift monitoring and intervention outcome feedback loop.
3. Integrate dashboards with cloud warehouse + IAM controls.

---
Generated on 2026-02-11T23:34:15.307047Z | Demo mode: True
