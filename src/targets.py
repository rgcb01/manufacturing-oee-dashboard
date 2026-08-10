from __future__ import annotations

from src.config import ManufacturingTargets, TARGETS


def target_for(kpi: str, targets: ManufacturingTargets = TARGETS) -> float:
    if kpi == "scrap_rate":
        return targets.scrap_rate_max
    return getattr(targets, kpi)


def delta_to_target(kpi: str, actual: float, targets: ManufacturingTargets = TARGETS) -> float:
    target = target_for(kpi, targets)
    return target - actual if kpi == "scrap_rate" else actual - target


def status_for(kpi: str, actual: float, targets: ManufacturingTargets = TARGETS) -> str:
    delta = delta_to_target(kpi, actual, targets)
    if delta >= 0:
        return "On Target"
    if delta >= -0.03:
        return "Watch"
    return "Below Target"
