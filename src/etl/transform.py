"""Transform and clean extracted data."""

from __future__ import annotations

import pandas as pd


def transform_data(
    student_info: pd.DataFrame,
    student_assessment: pd.DataFrame,
    assessments: pd.DataFrame,
) -> pd.DataFrame:
    merged = student_assessment.merge(assessments, on="id_assessment", how="left")
    merged = merged.merge(student_info, on="id_student", how="left")

    merged["week"] = (merged["date_submitted"].fillna(merged["date"]).fillna(0) // 7).astype(int)
    merged["score"] = merged["score"].fillna(0.0)
    merged["submitted"] = merged.get("submitted", 1)
    merged["submitted"] = merged["submitted"].fillna(1).astype(int)

    passthrough = [
        "id_student",
        "code_module",
        "week",
        "score",
        "submitted",
        "studied_credits",
        "age_band_num",
        "imd_band_num",
        "disability_flag",
        "pass_probability_base",
    ]
    for col in passthrough:
        if col not in merged.columns:
            merged[col] = 0

    return merged[passthrough].copy()
