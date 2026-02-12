"""Extract layer for OULAD raw data with demo fallback."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.config import PipelineConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)

EXPECTED_FILES = ["studentInfo.csv", "studentAssessment.csv", "assessments.csv"]


def _read_if_exists(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path) if path.exists() else None


def _generate_demo_data(config: PipelineConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(config.random_seed)
    n_students = 300
    student_ids = np.arange(10000, 10000 + n_students)
    courses = rng.choice(["AAA", "BBB", "CCC", "DDD"], size=n_students)
    risk_baseline = rng.beta(2, 5, size=n_students)

    student_info = pd.DataFrame(
        {
            "id_student": student_ids,
            "code_module": courses,
            "studied_credits": rng.integers(30, 120, size=n_students),
            "age_band_num": rng.integers(1, 4, size=n_students),
            "imd_band_num": rng.integers(1, 10, size=n_students),
            "disability_flag": rng.integers(0, 2, size=n_students),
            "pass_probability_base": np.clip(0.75 - risk_baseline * 0.6, 0.15, 0.95),
        }
    )

    records = []
    assess_rows = []
    aid = 1
    for wk in range(1, 11):
        assess_rows.append({"id_assessment": aid, "date": wk * 7, "weight": 10})
        scores = np.clip(70 - risk_baseline * 50 + rng.normal(0, 10, size=n_students), 0, 100)
        submitted = rng.binomial(1, np.clip(0.95 - risk_baseline * 0.5, 0.3, 0.99), size=n_students)
        for sid, score, sub in zip(student_ids, scores, submitted):
            records.append(
                {
                    "id_student": sid,
                    "id_assessment": aid,
                    "date_submitted": wk * 7,
                    "score": round(float(score), 2) if sub else np.nan,
                    "is_banked": 0,
                    "submitted": int(sub),
                }
            )
        aid += 1
    student_assessment = pd.DataFrame(records)
    assessments = pd.DataFrame(assess_rows)
    return student_info, student_assessment, assessments


def extract_data(config: PipelineConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    missing = [f for f in EXPECTED_FILES if not (config.data_raw_dir / f).exists()]
    if missing:
        msg = (
            "Raw OULAD files missing. Expected in data/raw: "
            + ", ".join(EXPECTED_FILES)
            + ". Running in demo mode with synthetic data."
        )
        logger.warning(msg)
        if not config.demo_mode:
            raise FileNotFoundError(
                msg + " Set PIPELINE_DEMO_MODE=true or place files in data/raw with expected names."
            )
        return _generate_demo_data(config)

    logger.info("Reading raw OULAD files from data/raw")
    info = _read_if_exists(config.data_raw_dir / "studentInfo.csv")
    assess = _read_if_exists(config.data_raw_dir / "studentAssessment.csv")
    assessments = _read_if_exists(config.data_raw_dir / "assessments.csv")
    if info is None or assess is None or assessments is None:
        raise FileNotFoundError("Could not read one or more required raw files.")
    return info, assess, assessments
