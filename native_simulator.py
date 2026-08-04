"""Optional C++ engine adapter that preserves the public Python data model."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import numpy as np

import parameters

if TYPE_CHECKING:
    from utility import ElectricData

try:
    import _terna_cpp
except ImportError:
    _terna_cpp = None


def cpp_available() -> bool:
    return _terna_cpp is not None


def use_cpp_engine() -> bool:
    return os.getenv("TERNA_SIMULATION_ENGINE", "python").lower() == "cpp" and cpp_available()


def parameter_snapshot() -> dict:
    return {
        "ETA_CHARGE": parameters.ETA_CHARGE,
        "ETA_DISCHARGE": parameters.ETA_DISCHARGE,
        "NUCLEAR_BASE_LOAD_FACTOR": parameters.NUCLEAR_BASE_LOAD_FACTOR,
        "STORAGE_CAPACITY_COST": parameters.STORAGE_CAPACITY_COST,
        "SOURCE_COSTS": dict(parameters.SOURCE_COSTS),
    }


def _series(data: ElectricData) -> dict[str, np.ndarray]:
    return {key: np.ascontiguousarray(values, dtype=np.float64) for key, values in data.power_item.items()}


def simulate(data: ElectricData, max_capacity: float, k_pv: float, k_w: float, nuke: bool) -> ElectricData:
    if _terna_cpp is None:
        raise RuntimeError("The C++ simulation extension is not available.")
    from utility import ElectricData

    result = _terna_cpp.simulate(_series(data), max_capacity, k_pv, k_w, nuke, parameter_snapshot())
    power_item = {
        key: np.asarray(result[key], dtype=np.float64)
        for key in parameters.SOURCES + parameters.OTHER_POWER_ITEMS
    }
    output = ElectricData(
        power_item=power_item,
        start=data.start,
        end=data.end,
        storage_capacity=max_capacity,
    )
    output.compute_peaks()
    duration_days = (output.end - output.start).days
    native_costs = _terna_cpp.energy_costs(_series(output), max_capacity, duration_days, parameter_snapshot())
    output.compute_energy()
    for source, values in native_costs.items():
        if source != "Total" and source in output.energy_item:
            output.energy_item[source] = (float(values[0]), float(values[1]))
    output.energy_item["Total Production"] = (
        sum(output.energy_item[source][0] for source in parameters.SOURCES),
        float(native_costs["Total"]),
    )
    return output


def decarbonization_surface(data: ElectricData, k_pv_range: float, k_w_range: float, capacity_range: float) -> list[tuple[float, float, float]]:
    if _terna_cpp is None:
        raise RuntimeError("The C++ simulation extension is not available.")
    return [
        (float(k_pv), float(k_w), float(capacity))
        for k_pv, k_w, capacity in _terna_cpp.decarbonization_surface(
            _series(data),
            k_pv_range,
            k_w_range,
            capacity_range,
            parameter_snapshot(),
            max(0, int(os.getenv("TERNA_SURFACE_WORKERS", "0"))),
        )
    ]


def nuclear_decarbonization_surface(data: ElectricData, k_pv_range: float, k_w_range: float) -> list[tuple[float, float, float, float]]:
    if _terna_cpp is None:
        raise RuntimeError("The C++ simulation extension is not available.")
    duration_days = (data.end - data.start).days
    return [
        (float(k_pv), float(k_w), float(nuclear_peak), float(annual_cost))
        for k_pv, k_w, nuclear_peak, annual_cost in _terna_cpp.nuclear_decarbonization_surface(
            _series(data),
            k_pv_range,
            k_w_range,
            duration_days,
            parameter_snapshot(),
            max(0, int(os.getenv("TERNA_SURFACE_WORKERS", "0"))),
        )
    ]


def load_csv(path: str, kind: str) -> tuple[dict[str, np.ndarray], str, str]:
    """Load one raw data CSV through the C++ parser and return Python-compatible values."""
    if _terna_cpp is None:
        raise RuntimeError("The C++ simulation extension is not available.")
    result = _terna_cpp.load_csv(path, kind)
    return (
        {key: np.asarray(values, dtype=np.float64) for key, values in result["series"].items()},
        str(result["start"]),
        str(result["end"]),
    )