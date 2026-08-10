from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ManufacturingTargets:
    oee: float = 0.85
    availability: float = 0.90
    performance: float = 0.95
    quality: float = 0.99
    scrap_rate_max: float = 0.02


TARGETS = ManufacturingTargets()

PERCENT_KPIS = ["oee", "availability", "performance", "quality", "scrap_rate"]
TARGET_LABELS = {
    "oee": "OEE",
    "availability": "Availability",
    "performance": "Performance",
    "quality": "Quality",
    "scrap_rate": "Scrap Rate",
}
