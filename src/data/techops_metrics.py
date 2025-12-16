"""Deterministic Tech Ops KPI metric generator for dashboard + investigations.

This module provides demo-ready time series data for:
- Daily KPIs (last 30 days; also supports YoY comparison)
- Weekly KPIs (rolling 53 weeks; supports YoY)

Design goals:
- Deterministic (seeded) so demos are repeatable
- Station-scoped
- Includes signal states (none/warning/critical) based on KPI thresholds
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List, Literal, Optional, Tuple

SignalState = Literal["none", "warning", "critical"]
AggType = Literal["mean", "sum"]


@dataclass(frozen=True)
class KPIDef:
    id: str
    label: str
    unit: str
    agg: AggType
    goal: float
    ul: float
    ll: float
    decimals: int


@dataclass(frozen=True)
class MetricPoint:
    # ISO date string (YYYY-MM-DD) for daily, or week_start for weekly
    t: str
    value: float
    yoy_value: Optional[float] = None
    yoy_delta: Optional[float] = None
    signal_state: SignalState = "none"


@dataclass
class KPISeries:
    kpi: KPIDef
    # last N points for requested window
    points: List[MetricPoint]
    # convenience summary
    mean: float
    past_value: float
    past_delta: float
    signal_state: SignalState


class TechOpsStore:
    """In-memory store holding generated demo data.

    For demo purposes we generate ~13 months of daily data per KPI per station.
    Weekly data is derived by aggregation.
    """

    def __init__(self, *, seed: int = 202489, today: Optional[date] = None):
        self.seed = seed
        self.today = today or date.today()
        self.kpis: Dict[str, KPIDef] = {}
        # station -> kpi_id -> daily points (oldest..newest)
        self.daily: Dict[str, Dict[str, List[Tuple[date, float]]]] = {}
        self.stations: List[str] = []

    def ensure_seeded(self) -> None:
        if self.kpis and self.daily:
            return
        self._seed_kpis()
        self._seed_data(stations=["DAL", "PHX", "HOU"])

    def _seed_kpis(self) -> None:
        # KPI definitions based on the measures you provided.
        # Units are intentionally generic and can be tuned later.
        self.kpis = {
            "OTP_MX_RATE": KPIDef("OTP_MX_RATE", "OTP MX Rate", "%", "mean", goal=2.0, ul=3.0, ll=1.0, decimals=2),
            "EMO_MX_RATE": KPIDef("EMO_MX_RATE", "EMO MX Rate", "%", "mean", goal=99.0, ul=99.5, ll=98.0, decimals=1),
            "MX_EXTREME_DELAY_RATE": KPIDef("MX_EXTREME_DELAY_RATE", "Extreme Delay MX Rate", "%", "mean", goal=1.0, ul=1.5, ll=0.5, decimals=2),
            "FAULT_RATE": KPIDef("FAULT_RATE", "Fault Rate", "rate", "mean", goal=0.5, ul=0.8, ll=0.2, decimals=2),
            "FINDING_RATE": KPIDef("FINDING_RATE", "Finding Rate", "rate", "mean", goal=2.0, ul=3.0, ll=1.0, decimals=2),
            "OTS_RATE": KPIDef("OTS_RATE", "OTS Rate", "rate", "mean", goal=0.05, ul=0.10, ll=0.01, decimals=3),
            "MEL_RATE": KPIDef("MEL_RATE", "MEL Rate", "rate", "mean", goal=0.25, ul=0.40, ll=0.10, decimals=3),
            "MEL_CX_RATE": KPIDef("MEL_CX_RATE", "MEL CX Rate", "rate", "mean", goal=0.06, ul=0.09, ll=0.03, decimals=3),
            "INJURY_COUNT": KPIDef("INJURY_COUNT", "Injury Counts", "count", "sum", goal=8.0, ul=12.0, ll=4.0, decimals=0),
            "PREMIUM_PAY_RATE": KPIDef("PREMIUM_PAY_RATE", "Premium Pay Rate", "%", "mean", goal=12.0, ul=15.0, ll=9.0, decimals=1),
        }

    def _seed_data(self, *, stations: List[str]) -> None:
        self.stations = stations
        self.daily = {s: {} for s in stations}

        # generate 395 days (~13 months) so YoY comparisons are available for last 30 days
        days = 395
        start = self.today - timedelta(days=days - 1)

        for station in stations:
            for kpi_id, kpi in self.kpis.items():
                series = self._generate_daily_series(station=station, kpi=kpi, start=start, days=days)
                self.daily[station][kpi_id] = series

    def _rng(self, station: str, kpi: KPIDef) -> random.Random:
        # Stable per-station per-kpi RNG
        salt = abs(hash(f"{station}:{kpi.id}:{self.seed}")) % (2**31 - 1)
        return random.Random(salt)

    def _generate_daily_series(self, *, station: str, kpi: KPIDef, start: date, days: int) -> List[Tuple[date, float]]:
        rng = self._rng(station, kpi)

        # Station-specific offset (subtle) so stations differ
        station_bias = (abs(hash(station)) % 13) / 100.0  # 0..0.12

        # Base level around goal (or slightly under/over depending on KPI)
        base = kpi.goal
        if "RATE" in kpi.id and kpi.unit in ("%", "rate"):
            base = kpi.goal * (0.95 + 0.10 * station_bias)
        if kpi.id == "EMO_MX_RATE":
            base = kpi.goal * (0.99 + 0.005 * station_bias)
        if kpi.id == "INJURY_COUNT":
            base = kpi.goal * (0.8 + 0.3 * station_bias)

        # Noise scale relative to goal
        noise = max(0.01, abs(kpi.goal) * 0.05)
        if kpi.id in ("OTS_RATE", "MEL_RATE", "MEL_CX_RATE"):
            noise = max(0.005, kpi.goal * 0.25)
        if kpi.id == "EMO_MX_RATE":
            noise = 0.4
        if kpi.id == "INJURY_COUNT":
            noise = 2.5

        points: List[Tuple[date, float]] = []

        # Deterministic “signal injection”: pick a few spike windows per KPI per station.
        # These spikes are placed near the most recent weeks so the dashboard always has something interesting.
        spike_days = set()
        if kpi.id in ("OTP_MX_RATE", "MEL_RATE", "MX_EXTREME_DELAY_RATE"):
            # 2 spikes in last 60 days
            for offset in (12, 34):
                spike_days.add(days - 1 - offset)
        if kpi.id in ("FAULT_RATE", "FINDING_RATE"):
            for offset in (18,):
                spike_days.add(days - 1 - offset)
        if kpi.id == "INJURY_COUNT":
            for offset in (7, 21):
                spike_days.add(days - 1 - offset)

        for i in range(days):
            d = start + timedelta(days=i)

            # weekly seasonality
            weekly = math.sin((2 * math.pi * d.weekday()) / 7.0)
            # annual-ish seasonality (rough)
            year_phase = (d.timetuple().tm_yday / 365.0) * 2 * math.pi
            annual = math.sin(year_phase)

            val = base + (weekly * noise * 0.25) + (annual * noise * 0.15) + rng.gauss(0, noise * 0.35)

            # clamp or shape per KPI
            if kpi.unit == "%":
                val = max(0.0, min(100.0, val))
            if kpi.id in ("OTS_RATE", "MEL_RATE", "MEL_CX_RATE", "FAULT_RATE", "FINDING_RATE"):
                val = max(0.0, val)

            # signal injection spikes
            if i in spike_days:
                if kpi.unit == "%":
                    val = min(100.0, val + noise * 2.5)
                elif kpi.agg == "sum":
                    val = max(0.0, val + 6)
                else:
                    val = max(0.0, val + noise * 2.0)

            # injury counts as integers
            if kpi.id == "INJURY_COUNT":
                val = max(0.0, round(val))

            points.append((d, float(val)))

        return points

    def get_kpis(self) -> List[KPIDef]:
        self.ensure_seeded()
        return list(self.kpis.values())

    def get_weekly_series(self, *, station: str, weeks: int = 53) -> Dict[str, KPISeries]:
        self.ensure_seeded()
        if station not in self.daily:
            raise KeyError(f"Unknown station: {station}")

        out: Dict[str, KPISeries] = {}
        for kpi_id, kpi in self.kpis.items():
            daily = self.daily[station][kpi_id]
            weekly_points = _aggregate_to_weeks(daily=daily, agg=kpi.agg)

            # keep last (weeks + 53) so YoY comparisons available
            weekly_points = weekly_points[-(weeks + 53) :]
            current = weekly_points[-weeks:]
            prev_year = weekly_points[:weeks] if len(weekly_points) >= (2 * weeks) else []

            pts: List[MetricPoint] = []
            for idx, (wk, v) in enumerate(current):
                yoy_v = None
                yoy_d = None
                if prev_year and idx < len(prev_year):
                    yoy_v = prev_year[idx][1]
                    yoy_d = v - yoy_v
                ss = _signal_state(value=v, kpi=kpi)
                pts.append(MetricPoint(t=wk.isoformat(), value=_round(v, kpi.decimals), yoy_value=_round(yoy_v, kpi.decimals) if yoy_v is not None else None, yoy_delta=_round(yoy_d, kpi.decimals) if yoy_d is not None else None, signal_state=ss))

            values = [p.value for p in pts] or [0.0]
            mean = sum(values) / len(values)
            past_value = pts[-1].value if pts else 0.0
            prev_value = pts[-2].value if len(pts) >= 2 else past_value
            past_delta = past_value - prev_value
            series_state = max((p.signal_state for p in pts), key=_signal_rank)
            out[kpi_id] = KPISeries(kpi=kpi, points=pts, mean=_round(mean, kpi.decimals), past_value=past_value, past_delta=_round(past_delta, kpi.decimals), signal_state=series_state)

        return out

    def get_daily_series(self, *, station: str, days: int = 30) -> Dict[str, KPISeries]:
        self.ensure_seeded()
        if station not in self.daily:
            raise KeyError(f"Unknown station: {station}")

        out: Dict[str, KPISeries] = {}
        for kpi_id, kpi in self.kpis.items():
            daily = self.daily[station][kpi_id]
            current = daily[-days:]

            # YoY for daily: compare to same day last year (approx 365 days earlier)
            lookup = {d: v for d, v in daily}
            pts: List[MetricPoint] = []
            for d, v in current:
                prev_d = d - timedelta(days=365)
                yoy_v = lookup.get(prev_d)
                yoy_d = (v - yoy_v) if yoy_v is not None else None
                ss = _signal_state(value=v, kpi=kpi)
                pts.append(
                    MetricPoint(
                        t=d.isoformat(),
                        value=_round(v, kpi.decimals),
                        yoy_value=_round(yoy_v, kpi.decimals) if yoy_v is not None else None,
                        yoy_delta=_round(yoy_d, kpi.decimals) if yoy_d is not None else None,
                        signal_state=ss,
                    )
                )

            values = [p.value for p in pts] or [0.0]
            mean = sum(values) / len(values)
            past_value = pts[-1].value if pts else 0.0
            prev_value = pts[-2].value if len(pts) >= 2 else past_value
            past_delta = past_value - prev_value
            series_state = max((p.signal_state for p in pts), key=_signal_rank)
            out[kpi_id] = KPISeries(kpi=kpi, points=pts, mean=_round(mean, kpi.decimals), past_value=past_value, past_delta=_round(past_delta, kpi.decimals), signal_state=series_state)

        return out


def _round(v: Optional[float], decimals: int) -> Optional[float]:
    if v is None:
        return None
    return float(round(v, decimals))


def _signal_state(*, value: float, kpi: KPIDef) -> SignalState:
    # For demo:
    # - critical if above UL (or below LL for “higher is better” KPIs like EMO)
    # - warning if beyond goal directionally
    if kpi.id == "EMO_MX_RATE":
        if value < kpi.ll:
            return "critical"
        if value < kpi.goal:
            return "warning"
        return "none"

    if value > kpi.ul:
        return "critical"
    if value > kpi.goal:
        return "warning"
    return "none"


def _signal_rank(state: SignalState) -> int:
    return {"none": 0, "warning": 1, "critical": 2}[state]


def _aggregate_to_weeks(*, daily: List[Tuple[date, float]], agg: AggType) -> List[Tuple[date, float]]:
    """Aggregate daily points into week-start buckets (Monday)."""
    buckets: Dict[date, List[float]] = {}
    for d, v in daily:
        wk = d - timedelta(days=d.weekday())  # Monday
        buckets.setdefault(wk, []).append(v)

    weeks = sorted(buckets.keys())
    out: List[Tuple[date, float]] = []
    for wk in weeks:
        vals = buckets[wk]
        if not vals:
            continue
        if agg == "sum":
            out.append((wk, float(sum(vals))))
        else:
            out.append((wk, float(sum(vals) / len(vals))))
    return out


# Global singleton for the API server
_GLOBAL_TECHOPS: Optional[TechOpsStore] = None


def get_techops_store() -> TechOpsStore:
    global _GLOBAL_TECHOPS
    if _GLOBAL_TECHOPS is None:
        _GLOBAL_TECHOPS = TechOpsStore()
        _GLOBAL_TECHOPS.ensure_seeded()
    return _GLOBAL_TECHOPS


