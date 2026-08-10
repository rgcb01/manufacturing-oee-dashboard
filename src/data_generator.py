from __future__ import annotations

import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


LINES = ["Line-A", "Line-B", "Line-C"]
SHIFTS = ["Shift-1", "Shift-2", "Shift-3"]
PRODUCTS = ["Housing", "Bracket", "Sensor Mount", "Connector"]
PRODUCT_CYCLE_TIMES = {
    "Housing": 42,
    "Bracket": 38,
    "Sensor Mount": 55,
    "Connector": 48,
}
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
        temporary_degradation = 12 <= day <= 16
        recovery_period = day >= 22
        for line in LINES:
            for shift_index, shift in enumerate(SHIFTS):
                planned_minutes = 480
                product = product_for_period(day, line, shift)
                ideal_cycle_time_sec = PRODUCT_CYCLE_TIMES[product]

                downtime_base = 35
                if line == "Line-C":
                    downtime_base += 18
                if line == "Line-C" and shift == "Shift-1":
                    downtime_base += 12
                if temporary_degradation and line in {"Line-B", "Line-C"}:
                    downtime_base += 22
                if recovery_period:
                    downtime_base -= 10

                downtime_minutes = max(0, int(random.gauss(downtime_base, 13)))
                downtime_minutes = min(downtime_minutes, 180)
                operating_minutes = planned_minutes - downtime_minutes

                target_units = int((operating_minutes * 60) / ideal_cycle_time_sec)
                performance_center = 0.91
                if product == "Sensor Mount":
                    performance_center -= 0.055
                if shift == "Shift-3":
                    performance_center -= 0.025
                if temporary_degradation:
                    performance_center -= 0.035
                if recovery_period:
                    performance_center += 0.025
                performance_factor = min(1.04, max(0.72, random.gauss(performance_center, 0.045)))
                total_units = max(0, int(target_units * performance_factor))

                scrap_rate = random.uniform(0.008, 0.028)
                if line == "Line-B" and shift == "Shift-2":
                    scrap_rate += random.uniform(0.015, 0.035)
                if product == "Connector":
                    scrap_rate += random.uniform(0.006, 0.014)
                if temporary_degradation and line == "Line-B":
                    scrap_rate += random.uniform(0.006, 0.018)
                if recovery_period:
                    scrap_rate = max(0.004, scrap_rate - random.uniform(0.004, 0.010))
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
                for duration in split_quantity(downtime_minutes, random.randint(1, 4)):
                    if duration <= 0:
                        continue
                    downtime_rows.append(
                        {
                            "date": date,
                            "line": line,
                            "shift": shift,
                            "product": product,
                            "reason": random.choice(DOWNTIME_REASONS),
                            "duration_minutes": duration,
                        }
                    )
                assign_dominant_downtime_reason(downtime_rows, date, line, shift)

                remaining_scrap = scrap_units
                for qty in split_quantity(scrap_units, random.randint(1, 3)):
                    if qty <= 0:
                        continue
                    scrap_rows.append(
                        {
                            "date": date,
                            "line": line,
                            "shift": shift,
                            "product": product,
                            "reason": random.choice(SCRAP_REASONS),
                            "quantity": qty,
                        }
                    )

    write_csv(output_dir / "synthetic_production_data.csv", production_rows)
    write_csv(output_dir / "downtime_events.csv", downtime_rows)
    write_csv(output_dir / "scrap_events.csv", scrap_rows)


def product_for_period(day: int, line: str, shift: str) -> str:
    if line == "Line-B" and shift == "Shift-2":
        return "Connector" if day % 2 == 0 else "Sensor Mount"
    index = (day + LINES.index(line) + SHIFTS.index(shift)) % len(PRODUCTS)
    return PRODUCTS[index]


def split_quantity(total: int, max_parts: int) -> list[int]:
    if total <= 0:
        return []
    parts = min(max_parts, total)
    remaining = total
    quantities = []
    for index in range(parts):
        if index == parts - 1:
            quantities.append(remaining)
        else:
            max_allowed = remaining - (parts - index - 1)
            quantity = random.randint(1, max_allowed)
            quantities.append(quantity)
            remaining -= quantity
    return quantities


def assign_dominant_downtime_reason(
    downtime_rows: list[dict[str, object]], date: str, line: str, shift: str
) -> None:
    """Make selected synthetic patterns discoverable without breaking sums."""
    matching_indexes = [
        index
        for index, row in enumerate(downtime_rows)
        if row["date"] == date and row["line"] == line and row["shift"] == shift
    ]
    if not matching_indexes:
        return
    if line == "Line-C":
        reason = "Maintenance"
    elif line == "Line-B" and shift == "Shift-2":
        reason = "Quality hold"
    else:
        return
    largest_index = max(matching_indexes, key=lambda idx: downtime_rows[idx]["duration_minutes"])
    downtime_rows[largest_index]["reason"] = reason


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
