from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


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
