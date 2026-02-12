"""Alerting logic: threshold and trend spike detection."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from src.config import PipelineConfig
from src.etl.load import DBClient


def generate_alert(
    latest_predictions: pd.DataFrame, features: pd.DataFrame, config: PipelineConfig, db: DBClient
) -> str:
    high_risk_rate = latest_predictions["high_risk_flag"].mean()

    week_mean = (
        features.groupby("week", as_index=False)["dropout_risk_target"].mean().sort_values("week")
    )
    if len(week_mean) >= 2:
        prior = week_mean.iloc[-2]["dropout_risk_target"]
        current = week_mean.iloc[-1]["dropout_risk_target"]
        spike_pct = (current - prior) / max(prior, 1e-9)
    else:
        spike_pct = 0.0

    threshold_triggered = high_risk_rate > config.high_risk_threshold
    spike_triggered = spike_pct > config.spike_threshold_pct
    top_10 = latest_predictions.head(10)["id_student"].astype(str).tolist()

    trigger_lines = []
    alert_type = "none"
    if threshold_triggered:
        trigger_lines.append(
            f"- Threshold alert: high-risk rate {high_risk_rate:.2%} > configured {config.high_risk_threshold:.2%}."
        )
        alert_type = "threshold"
    if spike_triggered:
        trigger_lines.append(
            f"- Spike alert: mean risk increased {spike_pct:.2%} WoW > configured {config.spike_threshold_pct:.2%}."
        )
        alert_type = "spike" if alert_type == "none" else "threshold_and_spike"
    if not trigger_lines:
        trigger_lines.append("- No alert triggered; metrics remain within configured limits.")

    body = f"""# Student Risk Alert Report

Generated: {datetime.utcnow().isoformat()}Z

## Trigger Summary
{chr(10).join(trigger_lines)}

## Summary Stats
- Current high-risk rate: **{high_risk_rate:.2%}**
- Week-over-week risk change: **{spike_pct:.2%}**
- Current week modeled students: **{len(latest_predictions)}**

## Top 10 At-Risk Student IDs
{chr(10).join([f'- {sid}' for sid in top_10])}

## Recommended Actions
1. Prioritize outreach to top risk students within 48 hours.
2. Provide tutoring nudges for low-score cohorts and low submission behavior.
3. Escalate course-level hotspots to academic advisors and module leaders.
4. Review intervention capacity and expected ROI before launching outreach.
"""
    out_path = config.alerts_dir / "alert_latest.md"
    out_path.write_text(body)

    db.execute(
        (
            "INSERT INTO alert_log (run_ts, alert_type, high_risk_rate, spike_pct, message) VALUES (?, ?, ?, ?, ?)"
            if db.driver == "sqlite"
            else "INSERT INTO alert_log (run_ts, alert_type, high_risk_rate, spike_pct, message) VALUES (%s, %s, %s, %s, %s)"
        ),
        (
            datetime.utcnow().isoformat(),
            alert_type,
            float(high_risk_rate),
            float(spike_pct),
            " | ".join(trigger_lines),
        ),
    )
    return body
