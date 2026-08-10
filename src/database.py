from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

DEFAULT_DB_PATH = Path("data/manufacturing.db")


def build_database(data_dir: Path, db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tables = {
        "production": data_dir / "synthetic_production_data.csv",
        "downtime": data_dir / "downtime_events.csv",
        "scrap": data_dir / "scrap_events.csv",
    }
    with sqlite3.connect(db_path) as connection:
        for table_name, csv_path in tables.items():
            pd.read_csv(csv_path).to_sql(table_name, connection, if_exists="replace", index=False)


def load_table(db_path: Path, table_name: str) -> pd.DataFrame:
    with sqlite3.connect(db_path) as connection:
        return pd.read_sql_query(f"SELECT * FROM {table_name}", connection, parse_dates=["date"])


def load_manufacturing_data(db_path: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load production, downtime and scrap records from SQLite."""
    return (
        load_table(db_path, "production"),
        load_table(db_path, "downtime"),
        load_table(db_path, "scrap"),
    )


def load_csv_data(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load portfolio CSV files when SQLite has not been built yet."""
    return (
        pd.read_csv(data_dir / "synthetic_production_data.csv", parse_dates=["date"]),
        pd.read_csv(data_dir / "downtime_events.csv", parse_dates=["date"]),
        pd.read_csv(data_dir / "scrap_events.csv", parse_dates=["date"]),
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Build SQLite database from CSV data.")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()
    build_database(args.data_dir, args.db_path)


if __name__ == "__main__":
    main()
