"""Load OULAD raw CSV files into Postgres raw.* tables."""

from __future__ import annotations

import os
from pathlib import Path

import psycopg2

RAW_TABLE_SPECS = [
    ("studentInfo.csv", "student_info", True),
    ("studentAssessment.csv", "student_assessment", True),
    ("assessments.csv", "assessments", True),
    ("studentVle.csv", "student_vle", False),
    ("vle.csv", "vle", False),
    ("courses.csv", "courses", False),
    ("studentRegistration.csv", "student_registration", False),
]


def _normalized_database_url() -> str:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set for raw Postgres ingestion.")
    return database_url.replace("postgresql+psycopg2://", "postgresql://")


def _create_table_from_csv(cur, csv_path: Path, schema: str, table_name: str) -> list[str]:
    header_line = csv_path.read_text(encoding="utf-8").splitlines()[0]
    columns = [col.strip() for col in header_line.split(",")]
    col_sql = ", ".join(f'"{col}" TEXT' for col in columns)
    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    cur.execute(f"DROP TABLE IF EXISTS {schema}.{table_name}")
    cur.execute(f"CREATE TABLE {schema}.{table_name} ({col_sql})")
    return columns


def _copy_csv_into_table(
    cur, csv_path: Path, schema: str, table_name: str, columns: list[str]
) -> None:
    col_names = ", ".join(f'"{col}"' for col in columns)
    copy_sql = (
        f"COPY {schema}.{table_name} ({col_names}) "
        "FROM STDIN WITH (FORMAT CSV, HEADER TRUE, DELIMITER ',', QUOTE '\"')"
    )
    with csv_path.open("r", encoding="utf-8") as handle:
        cur.copy_expert(copy_sql, handle)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    raw_dir = repo_root / "data" / "raw"
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw directory not found: {raw_dir}")

    conn = psycopg2.connect(_normalized_database_url())
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                print("Connected to Postgres")

                for csv_name, table_name, required in RAW_TABLE_SPECS:
                    csv_path = raw_dir / csv_name
                    if not csv_path.exists():
                        if required:
                            raise FileNotFoundError(
                                f"Required raw file is missing: {csv_path}. "
                                "Required files: studentInfo.csv, studentAssessment.csv, assessments.csv"
                            )
                        print(f"Skipping optional file (not found): {csv_name}")
                        continue

                    columns = _create_table_from_csv(
                        cur, csv_path, schema="raw", table_name=table_name
                    )
                    _copy_csv_into_table(
                        cur, csv_path, schema="raw", table_name=table_name, columns=columns
                    )

                    cur.execute(f"SELECT COUNT(*) FROM raw.{table_name}")
                    row_count = cur.fetchone()[0]
                    print(f"Loaded raw.{table_name}: {row_count} rows")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
