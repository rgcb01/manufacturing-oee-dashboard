from __future__ import annotations

import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


LINES = ["Line-A", "Line-B", "Line-C"]
SHIFTS = ["Shift-1", "Shift-2", "Shift-3"]
PRODUCTS = ["Housing", "Bracket", "Sensor Mount", "Connector"]
DOWNTIME_REASONS = [
    "Changeover",
    "Material shortage",
    "Minor stop",
    "Quality hold",
    "Maintenance",
    "Tooling adjustment",
]
SCRAP_REASONS = [
    "Dimensional out-of-spec",
    "Surface defect",
    "Assembly misalignment",
    "Missing component",
    "Handling damage",
]


def generate_data(output_dir: Path, days: int = 30, seed: int = 42) -> None:
    random.seed(seed)
    output_dir.mkdir(parents=True, exist_ok=True)

    production_rows = []
    downtime_rows = []
    scrap_rows = []
    start_date = datetime(2026, 7, 1)

    for day in range(days):
        date = (start_date + timedelta(days=day)).date().isoformat()
        for line in LINES:
            for shift_index, shift in enumerate(SHIFTS):
                planned_minutes = 480
                product = random.choice(PRODUCTS)
                ideal_cycle_time_sec = random.choice([38, 42, 48, 55])

                downtime_minutes = max(0, int(random.gauss(42, 24)))
                downtime_minutes = min(downtime_minutes, 180)
                operating_minutes = planned_minutes - downtime_minutes

                target_units = int((operating_minutes * 60) / ideal_cycle_time_sec)
                performance_factor = random.uniform(0.78, 1.01)
                total_units = max(0, int(target_units * performance_factor))

                scrap_rate = random.uniform(0.008, 0.055)
                if line == "Line-B" and shift == "Shift-2":
                    scrap_rate += random.uniform(0.015, 0.035)
                scrap_units = int(total_units * scrap_rate)
                good_units = total_units - scrap_units

                production_rows.append(
                    {
                        "date": date,
                        "line": line,
                        "shift": shift,
                        "product": product,
                        "planned_minutes": planned_minutes,
                        "downtime_minutes": downtime_minutes,
                        "operating_minutes": operating_minutes,
                        "ideal_cycle_time_sec": ideal_cycle_time_sec,
                        "total_units": total_units,
                        "good_units": good_units,
                        "scrap_units": scrap_units,
                    }
                )

                remaining_downtime = downtime_minutes
                event_count = random.randint(1, 4) if downtime_minutes else 0
                for event_id in range(event_count):
                    if event_id == event_count - 1:
                        duration = remaining_downtime
                    else:
                        duration = random.randint(3, max(3, remaining_downtime // 2))
                    remaining_downtime -= duration
                    if duration <= 0:
                        continue
                    downtime_rows.append(
                        {
                            "date": date,
                            "line": line,
                            "shift": shift,
                            "reason": random.choice(DOWNTIME_REASONS),
                            "duration_minutes": duration,
                        }
                    )

                remaining_scrap = scrap_units
                scrap_event_count = random.randint(1, 3) if scrap_units else 0
                for event_id in range(scrap_event_count):
                    if event_id == scrap_event_count - 1:
                        qty = remaining_scrap
                    else:
                        qty = random.randint(1, max(1, remaining_scrap // 2))
                    remaining_scrap -= qty
                    if qty <= 0:
                        continue
                    scrap_rows.append(
                        {
                            "date": date,
                            "line": line,
                            "shift": shift,
                            "reason": random.choice(SCRAP_REASONS),
                            "quantity": qty,
                        }
                    )

    write_csv(output_dir / "synthetic_production_data.csv", production_rows)
    write_csv(output_dir / "downtime_events.csv", downtime_rows)
    write_csv(output_dir / "scrap_events.csv", scrap_rows)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic manufacturing data.")
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    generate_data(args.output_dir, days=args.days, seed=args.seed)


if __name__ == "__main__":
    main()
