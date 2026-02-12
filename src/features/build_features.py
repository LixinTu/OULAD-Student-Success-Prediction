"""Feature engineering with weekly time slicing."""

from __future__ import annotations

import numpy as np
import pandas as pd


def build_time_sliced_features(clean_df: pd.DataFrame) -> pd.DataFrame:
    clean_df = clean_df.sort_values(["id_student", "week"]).copy()
    grouped = clean_df.groupby(["id_student", "week", "code_module"], as_index=False).agg(
        weekly_score_mean=("score", "mean"),
        weekly_submissions=("submitted", "sum"),
        studied_credits=("studied_credits", "max"),
        age_band_num=("age_band_num", "max"),
        imd_band_num=("imd_band_num", "max"),
        disability_flag=("disability_flag", "max"),
        pass_probability_base=("pass_probability_base", "max"),
    )

    grouped["cum_submissions"] = grouped.groupby("id_student")["weekly_submissions"].cumsum()
    grouped["rolling_score_3w"] = grouped.groupby("id_student")["weekly_score_mean"].transform(
        lambda s: s.rolling(3, min_periods=1).mean()
    )
    grouped["score_trend_2w"] = grouped.groupby("id_student")["weekly_score_mean"].diff().fillna(0)

    score_factor = 1 - (grouped["rolling_score_3w"] / 100)
    submit_factor = np.clip(
        1 - grouped["cum_submissions"] / (grouped["week"].clip(lower=1) * 1.5), 0, 1
    )
    grouped["dropout_risk_target"] = (
        0.6 * score_factor
        + 0.2 * submit_factor
        + 0.2 * (1 - grouped["pass_probability_base"].clip(0.05, 0.99))
    )
    grouped["dropout_risk_target"] = grouped["dropout_risk_target"].clip(0, 1)
    grouped["target_high_risk"] = (grouped["dropout_risk_target"] > 0.45).astype(int)
    return grouped
