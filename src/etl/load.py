"""Load cleaned datasets to processed storage and database."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

import pandas as pd

from src.config import PipelineConfig
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DBClient:
    conn: object
    driver: str  # sqlite|postgres

    def execute(self, sql: str, params: tuple | None = None) -> None:
        cur = self.conn.cursor()
        cur.execute(sql, params or ())
        self.conn.commit()

    def insert_df(self, table_name: str, df: pd.DataFrame) -> None:
        if df.empty:
            return
        if self.driver == "sqlite":
            df.to_sql(table_name, self.conn, if_exists="append", index=False)
            return
        cols = list(df.columns)
        values = [tuple(x) for x in df.itertuples(index=False, name=None)]
        placeholders = ", ".join(["%s"] * len(cols))
        col_names = ", ".join(cols)
        query = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
        cur = self.conn.cursor()
        cur.executemany(query, values)
        self.conn.commit()


def get_database_client(config: PipelineConfig) -> DBClient:
    if config.database_url:
        import psycopg2

        normalized_url = config.database_url.replace("postgresql+psycopg2://", "postgresql://")
        conn = psycopg2.connect(normalized_url)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        logger.info("Connected to Postgres database")
        return DBClient(conn=conn, driver="postgres")

    conn = sqlite3.connect(config.db_path)
    logger.info("Using SQLite fallback at %s", config.db_path)
    return DBClient(conn=conn, driver="sqlite")


def initialize_schema(config: PipelineConfig, db: DBClient) -> None:
    schema_sql = (config.repo_root / "db" / "schema.sql").read_text()
    statements = [stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()]
    for stmt in statements:
        db.execute(stmt)


def load_processed_data(clean_df: pd.DataFrame, config: PipelineConfig, db: DBClient) -> None:
    clean_df.to_csv(config.data_processed_dir / "clean_events.csv", index=False)
    if db.driver == "sqlite":
        clean_df.to_sql("clean_events", db.conn, if_exists="replace", index=False)
