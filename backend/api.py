import sys
from pathlib import Path
import os
import math
import time
from collections import defaultdict, deque

# Make the parent directory (project root) importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

import parameters as params_module
import simulator as sim_module
from utility import load_power_data_from_npz, to_energy, compute_peaks, PowerData, EnergyData

NPZ_PATH = Path(__file__).parent.parent / "power_2025.npz"

app = FastAPI(title="Terna Energy Simulator API")

_cors_origins_raw = os.getenv("CORS_ALLOW_ORIGINS", "*")
_cors_origins = [origin.strip() for origin in _cors_origins_raw.split(",") if origin.strip()]

RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "120"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
_rate_buckets: dict[str, deque[float]] = defaultdict(deque)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# ── Power data (loaded once at startup) ───────────────────────────────────────
_power_data_2025: PowerData | None = None

@app.on_event("startup")
async def _load_power_data():
    """Load power data from NPZ file once at application startup."""
    global _power_data_2025
    _power_data_2025 = load_power_data_from_npz(NPZ_PATH)
    print(f"✓ Power data (2025) loaded from {NPZ_PATH}")

# ── Immutable defaults (captured once at startup) ─────────────────────────────
_DEFAULTS: dict[str, float] = {
    "ETA_CHARGE":               params_module.ETA_CHARGE,
    "ETA_DISCHARGE":            params_module.ETA_DISCHARGE,
    "NUCLEAR_BASE_LOAD_FACTOR": params_module.NUCLEAR_BASE_LOAD_FACTOR,
    "THERMAL_LCOE":             params_module.THERMAL_LCOE,
    "PV_LCOE":                  params_module.PV_LCOE,
    "WIND_LCOE":                params_module.WIND_LCOE,
    "NUKE_LCOE":                params_module.NUKE_LCOE,
    "LCOS":                     params_module.LCOS,
    "IMPORT_COST":              params_module.IMPORT_COST,
}

# Mutable session config (starts from defaults)
_config: dict[str, float] = dict(_DEFAULTS)

# Mapping from config key to SOURCE_COSTS dictionary key
_SOURCE_COST_MAP = {
    "THERMAL_LCOE": "Thermal",
    "PV_LCOE":      "Photovoltaic",
    "WIND_LCOE":    "Wind",
    "NUKE_LCOE":    "Nuclear",
    "LCOS":         "Storage",
    "IMPORT_COST":  "Net Import",
}

PARAM_METADATA = {
    "ETA_CHARGE": {
        "label": "Rendimento di carica",
        "unit": "adimensionale [0–1]",
        "description": (
            "Efficienza con cui l'energia elettrica viene convertita in energia immagazzinata "
            "durante la fase di carica del sistema di accumulo."
        ),
        "rationale": (
            "Valore tipico per batterie agli ioni di litio e sistemi di pompaggio idroelettrico, "
            "che presentano rendimenti di carica nell'intervallo 0.85–0.95."
        ),
    },
    "ETA_DISCHARGE": {
        "label": "Rendimento di scarica",
        "unit": "adimensionale [0–1]",
        "description": (
            "Efficienza con cui l'energia immagazzinata viene riconvertita in energia elettrica "
            "durante la fase di scarica del sistema di accumulo."
        ),
        "rationale": (
            "Il prodotto ETA_CHARGE × ETA_DISCHARGE fornisce il round-trip efficiency del sistema, "
            "pari a 0.81 con i valori di default."
        ),
    },
    "NUCLEAR_BASE_LOAD_FACTOR": {
        "label": "Fattore di carico base del nucleare",
        "unit": "adimensionale [0–1]",
        "description": (
            "Frazione della potenza di picco nucleare che il reattore mantiene come produzione "
            "minima garantita (base load), indipendentemente dalla domanda."
        ),
        "rationale": (
            "I reattori moderni operano tipicamente tra il 70% e il 90% della capacità nominale. "
            "Il valore del 30% è conservativo e riflette la flessibilità operativa dei nuovi impianti SMR."
        ),
    },
    "THERMAL_LCOE": {
        "label": "LCOE Termico",
        "unit": "€/GWh",
        "description": (
            "Costo livellato dell'energia elettrica da fonti termoelettriche (gas naturale, carbone). "
            "Include costi di costruzione, esercizio e combustibile."
        ),
        "rationale": (
            "Fonte: EIA Annual Energy Outlook – "
            "https://www.eia.gov/outlooks/aeo/electricity_generation/pdf/LCOE_report.pdf"
        ),
    },
    "PV_LCOE": {
        "label": "LCOE Fotovoltaico",
        "unit": "€/GWh",
        "description": "Costo livellato dell'energia elettrica da impianti fotovoltaici utility-scale.",
        "rationale": (
            "Fonte: EIA Annual Energy Outlook. Il PV è attualmente la fonte di nuova generazione "
            "più economica in molte regioni del mondo."
        ),
    },
    "WIND_LCOE": {
        "label": "LCOE Eolico",
        "unit": "€/GWh",
        "description": "Costo livellato dell'energia elettrica da impianti eolici onshore.",
        "rationale": "Fonte: EIA Annual Energy Outlook.",
    },
    "NUKE_LCOE": {
        "label": "LCOE Nucleare",
        "unit": "€/GWh",
        "description": (
            "Costo livellato dell'energia elettrica da impianti nucleari. "
            "Include costi di costruzione (elevati), esercizio, combustibile e smaltimento rifiuti."
        ),
        "rationale": (
            "Fonte: EIA Annual Energy Outlook. Il nucleare presenta LCOE superiore a PV ed eolico, "
            "ma garantisce continuità di fornitura (dispatchability)."
        ),
    },
    "LCOS": {
        "label": "LCOS – Costo livellato dell'accumulo",
        "unit": "€/GWh",
        "description": (
            "Costo livellato dello stoccaggio energetico (Levelized Cost of Storage). "
            "Rappresenta il costo per ogni GWh immagazzinato e rilasciato nel ciclo di vita del sistema."
        ),
        "rationale": (
            "Fonte: PNNL Energy Storage Cost Performance – "
            "https://www.pnnl.gov/projects/esgc-cost-performance/lcos-estimates. "
            "Include batterie, pompaggio idroelettrico e altri vettori."
        ),
    },
    "IMPORT_COST": {
        "label": "Costo medio importazione elettrica",
        "unit": "€/GWh",
        "description": "Prezzo medio pagato dall'Italia per l'elettricità importata dall'estero.",
        "rationale": (
            "Fonte: World Bank WITS Comtrade data, media 2024 sulle importazioni italiane "
            "di energia elettrica (voce HS 271600)."
        ),
    },
}


# ── Helpers ───────────────────────────────────────────────────────────────────

_PARAM_BOUNDS: dict[str, tuple[float, float]] = {
    "ETA_CHARGE": (0.0, 1.0),
    "ETA_DISCHARGE": (0.0, 1.0),
    "NUCLEAR_BASE_LOAD_FACTOR": (0.0, 1.0),
    "THERMAL_LCOE": (0.0, 2_000_000.0),
    "PV_LCOE": (0.0, 2_000_000.0),
    "WIND_LCOE": (0.0, 2_000_000.0),
    "NUKE_LCOE": (0.0, 2_000_000.0),
    "LCOS": (0.0, 2_000_000.0),
    "IMPORT_COST": (0.0, 2_000_000.0),
}


def _get_client_ip(request: Request) -> str:
    # We trust headers injected by our internal Nginx container.
    real_ip = request.headers.get("x-real-ip", "").strip()
    if real_ip:
        return real_ip
    xff = request.headers.get("x-forwarded-for", "").strip()
    if xff:
        return xff.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        ip = _get_client_ip(request)
        now = time.time()
        bucket = _rate_buckets[ip]
        while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT_REQUESTS:
            retry_after = max(1, int(RATE_LIMIT_WINDOW_SECONDS - (now - bucket[0])))
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please retry later."},
                headers={"Retry-After": str(retry_after)},
            )
        bucket.append(now)
    return await call_next(request)

def _apply_config() -> None:
    """Push current _config values into both params_module and sim_module namespaces."""
    for key, value in _config.items():
        setattr(params_module, key, value)
        # sim_module imported ETA_CHARGE etc. by name; patch its namespace too
        if hasattr(sim_module, key):
            setattr(sim_module, key, value)
    # SOURCE_COSTS is a mutable dict shared by reference with sim_module;
    # updating it in params_module is sufficient.
    for param_key, source_key in _SOURCE_COST_MAP.items():
        params_module.SOURCE_COSTS[source_key] = _config[param_key]


def _power_data_to_dict(data: PowerData) -> dict:
    n = len(next(iter(data.power_item.values())))
    return {
        "start": data.start.isoformat(),
        "step_minutes": 15,
        "n": n,
        "series": {k: v.tolist() for k, v in data.power_item.items()},
        "peaks": {
            k: {"value": float(v[0]), "time": v[1]}
            for k, v in data.power_peaks.items()
        },
    }


def _energy_to_dict(energy: EnergyData) -> dict:
    return {
        key: {"energy": float(energy_value), "cost": float(cost_value)}
        for key, (energy_value, cost_value) in energy.energy_item.items()
    }


def _differential_costs(before: EnergyData, after: EnergyData) -> dict[str, float]:
    """Return annual cost changes by source from the two energy summaries."""
    sources = {**before.energy_item, **after.energy_item}
    return {
        source: after.energy_item.get(source, (0.0, 0.0))[1]
        - before.energy_item.get(source, (0.0, 0.0))[1]
        for source in sources
        if source not in {"Total Production", "Curtailment"}
    }


def _get_power_data_copy() -> PowerData:
    """Return a shallow copy of the preloaded power data with fresh numpy array copies for power_item."""
    if _power_data_2025 is None:
        raise RuntimeError("Power data not yet loaded. Application startup may not have completed.")
    # Create a shallow copy of the PowerData but with deep copies of the arrays
    return PowerData(
        power_item={k: v.copy() for k, v in _power_data_2025.power_item.items()},
        power_peaks={},  # Will be recalculated
        start=_power_data_2025.start,
        end=_power_data_2025.end,
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/api/parameters")
def get_parameters():
    return [
        {
            "key": key,
            "label": PARAM_METADATA[key]["label"],
            "unit": PARAM_METADATA[key]["unit"],
            "default": _DEFAULTS[key],
            "current": _config[key],
            "description": PARAM_METADATA[key]["description"],
            "rationale": PARAM_METADATA[key]["rationale"],
        }
        for key in PARAM_METADATA
    ]


class ParameterUpdate(BaseModel):
    key: str
    value: float

    @field_validator("value")
    @classmethod
    def value_must_be_finite(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("Value must be a finite number.")
        return v


@app.patch("/api/parameters")
def update_parameter(update: ParameterUpdate):
    if update.key not in _config:
        raise HTTPException(status_code=404, detail=f"Parameter '{update.key}' not found.")
    min_v, max_v = _PARAM_BOUNDS[update.key]
    if not (min_v <= update.value <= max_v):
        raise HTTPException(
            status_code=422,
            detail=f"Parameter '{update.key}' out of range: expected [{min_v}, {max_v}].",
        )
    _config[update.key] = update.value
    _apply_config()
    return {"key": update.key, "value": _config[update.key]}


@app.post("/api/parameters/reset")
def reset_parameters():
    _config.update(_DEFAULTS)
    _apply_config()
    return get_parameters()


class SimulationRequest(BaseModel):
    max_capacity: float = Field(default=100.0, ge=0.0, le=5_000.0)
    k_pv: float = Field(default=3.0, ge=0.0, le=20.0)
    k_w: float = Field(default=2.0, ge=0.0, le=20.0)
    nuke: bool = True

    @field_validator("max_capacity", "k_pv", "k_w")
    @classmethod
    def numeric_fields_must_be_finite(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("Numeric field must be finite.")
        return v


@app.get("/api/current-scenario")
def get_current_scenario():
    _apply_config()
    power_data = _get_power_data_copy()
    compute_peaks(power_data)
    energy = to_energy(power_data)
    
    return {
        "chart": _power_data_to_dict(power_data),
        "energy": _energy_to_dict(energy),
    }


@app.post("/api/simulate")
def run_simulation(req: SimulationRequest):
    _apply_config()
    power_data = _get_power_data_copy()
    compute_peaks(power_data)
    energy_before = to_energy(power_data)

    power_after, energy_after = sim_module.simulate_alternative_scenario(
        power_in=power_data,
        max_capacity=req.max_capacity,
        k_pv=req.k_pv,
        k_w=req.k_w,
        nuke=req.nuke,
    )

    return {
        "before": {
            "chart": _power_data_to_dict(power_data),
            "energy": _energy_to_dict(energy_before),
        },
        "after": {
            "chart": _power_data_to_dict(power_after),
            "energy": _energy_to_dict(energy_after),
        },
        "costs": _differential_costs(energy_before, energy_after),
    }


# Static frontend (production)
_FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

if _FRONTEND_DIST.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(_FRONTEND_DIST), html=True),
        name="frontend",
    )
