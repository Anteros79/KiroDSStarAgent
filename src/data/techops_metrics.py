"""Deterministic Tech Ops KPI metric generator for dashboard + investigations.

This module provides demo-ready time series data for:
- Daily KPIs (last 30 days; also supports YoY comparison)
- Weekly KPIs (rolling 53 weeks; supports YoY)

Design goals:
- Deterministic (seeded) so demos are repeatable
- Station-scoped
- Includes signal states (none/warning/critical) using Wheeler XmR rules
"""

from __future__ import annotations

import math
import random
import hashlib
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List, Literal, Optional, Tuple

from src.spc.wheeler import XmRLimits, calculate_xmr_limits, detect_xmr_phases, wheeler_signal_state

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
    # Phase-aware limits (Wheeler XmR phases)
    cl: Optional[float] = None
    ucl: Optional[float] = None
    lcl: Optional[float] = None
    phase_number: Optional[int] = None
    # Demo-only root-cause label (used by diagnostic tests; not required for dashboard display)
    root_cause: Optional[str] = None


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
    # Wheeler XmR natural process limits computed over this window
    npl_cl: float
    npl_ucl: float
    npl_lcl: float
    npl_sigma: float
    npl_mr_bar: float


REGION_BY_STATION: Dict[str, str] = {"DAL": "SOUTH_CENTRAL", "HOU": "SOUTH_CENTRAL", "PHX": "WEST"}


def _stations_for_summary_level(stations: List[str], *, station: str, summary_level: str) -> List[str]:
    level = (summary_level or "station").lower()
    if level == "company":
        return list(stations)
    if level == "region":
        region = REGION_BY_STATION.get(station)
        if not region:
            return [station]
        return [s for s in stations if REGION_BY_STATION.get(s) == region] or [station]
    return [station]


def _aggregate_values(values: List[float], *, agg: AggType) -> float:
    if not values:
        return 0.0
    if agg == "sum":
        return float(sum(values))
    return float(sum(values) / len(values))


def _build_metric_points(
    *,
    t_values: List[str],
    values: List[float],
    yoy_values: List[Optional[float]],
    yoy_deltas: List[Optional[float]],
    decimals: int,
    clamp_lcl_at_zero: bool = True,
    min_baseline: int = 20,
) -> tuple[list[MetricPoint], XmRLimits]:
    phases, limits_by_index = detect_xmr_phases(
        values,
        min_baseline=min_baseline,
        clamp_lcl_at_zero=clamp_lcl_at_zero,
    )
    # Last-phase limits are the correct "current" limits (Wheeler)
    last_limits = limits_by_index[-1] if limits_by_index else calculate_xmr_limits(values, clamp_lcl_at_zero=clamp_lcl_at_zero)

    # Build quick lookup for phase number by index
    phase_number_by_index: List[int] = [1 for _ in values]
    for ph in phases:
        for idx in range(ph.start_index, ph.end_index + 1):
            if 0 <= idx < len(phase_number_by_index):
                phase_number_by_index[idx] = ph.phase_number

    pts: List[MetricPoint] = []
    for idx, (t, v, yoy_v, yoy_d) in enumerate(zip(t_values, values, yoy_values, yoy_deltas)):
        lim = limits_by_index[idx] if idx < len(limits_by_index) else last_limits
        is_rule1 = bool(v > lim.ucl or v < lim.lcl)
        pts.append(
            MetricPoint(
                t=t,
                value=float(_round(v, decimals) or 0.0),
                yoy_value=_round(yoy_v, decimals) if yoy_v is not None else None,
                yoy_delta=_round(yoy_d, decimals) if yoy_d is not None else None,
                signal_state="critical" if is_rule1 else "none",
                cl=float(_round(lim.cl, decimals) or 0.0),
                ucl=float(_round(lim.ucl, decimals) or 0.0),
                lcl=float(_round(lim.lcl, decimals) or 0.0),
                phase_number=phase_number_by_index[idx] if idx < len(phase_number_by_index) else 1,
            )
        )

    return pts, last_limits


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
        # station -> kpi_id -> date -> root cause label
        self.daily_root_causes: Dict[str, Dict[str, Dict[date, str]]] = {}
        # station -> kpi_id -> week_start -> root cause label
        self.weekly_root_causes: Dict[str, Dict[str, Dict[date, str]]] = {}
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
        self.daily_root_causes = {s: {} for s in stations}
        self.weekly_root_causes = {s: {} for s in stations}

        # generate 395 days (~13 months) so YoY comparisons are available for last 30 days
        days = 395
        start = self.today - timedelta(days=days - 1)

        for station in stations:
            for kpi_id, kpi in self.kpis.items():
                series = self._generate_daily_series(station=station, kpi=kpi, start=start, days=days)
                self.daily[station][kpi_id] = series

        self._compute_weekly_root_causes()

    def _compute_weekly_root_causes(self) -> None:
        for station in self.stations:
            self.weekly_root_causes.setdefault(station, {})
            for kpi_id in self.kpis.keys():
                day_map = self.daily_root_causes.get(station, {}).get(kpi_id, {})
                buckets: Dict[date, Dict[str, int]] = {}
                for d, cause in day_map.items():
                    wk = d - timedelta(days=d.weekday())
                    buckets.setdefault(wk, {})
                    buckets[wk][cause] = buckets[wk].get(cause, 0) + 1
                wk_map: Dict[date, str] = {}
                for wk, counts in buckets.items():
                    # pick most common cause in the week
                    cause = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
                    wk_map[wk] = cause
                self.weekly_root_causes[station][kpi_id] = wk_map

    def get_root_cause(
        self,
        *,
        kpi_id: str,
        station: str,
        window: str,
        t: Optional[str],
        summary_level: str = "station",
    ) -> Optional[str]:
        if not t:
            return None
        try:
            d = date.fromisoformat(t[:10])
        except Exception:
            return None

        scope = _stations_for_summary_level(self.stations, station=station, summary_level=summary_level)
        labels: List[str] = []
        if window == "weekly":
            for st in scope:
                wk_map = self.weekly_root_causes.get(st, {}).get(kpi_id, {})
                labels.append(wk_map.get(d) or "")
        else:
            for st in scope:
                day_map = self.daily_root_causes.get(st, {}).get(kpi_id, {})
                labels.append(day_map.get(d) or "")
        labels = [x for x in labels if x]
        if not labels:
            return None
        # If multiple stations have different causes, summarize.
        counts: Dict[str, int] = {}
        for c in labels:
            counts[c] = counts.get(c, 0) + 1
        ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        if len(ranked) == 1:
            return ranked[0][0]
        top = ", ".join([f"{c} (x{n})" for c, n in ranked[:2]])
        return f"Mixed causes across scope: {top}"

    def _rng(self, station: str, kpi: KPIDef) -> random.Random:
        # Stable per-station per-kpi RNG (do NOT use Python's built-in hash; it's process-randomized).
        key = f"{station}:{kpi.id}:{self.seed}".encode("utf-8")
        digest = hashlib.blake2b(key, digest_size=8).digest()
        salt = int.from_bytes(digest, byteorder="big", signed=False)
        return random.Random(salt)

    def _generate_daily_series(self, *, station: str, kpi: KPIDef, start: date, days: int) -> List[Tuple[date, float]]:
        rng = self._rng(station, kpi)

        # Station-specific offset (subtle) so stations differ
        station_digest = hashlib.blake2b(station.encode("utf-8"), digest_size=2).digest()
        station_bias = (int.from_bytes(station_digest, byteorder="big", signed=False) % 13) / 100.0  # 0..0.12

        # Base level around goal (or slightly under/over depending on KPI).
        # For SUM-type KPIs, interpret the goal as a weekly target and scale to daily.
        base = (kpi.goal / 7.0) if kpi.agg == "sum" else kpi.goal
        if "RATE" in kpi.id and kpi.unit in ("%", "rate"):
            base = kpi.goal * (0.95 + 0.10 * station_bias)
        if kpi.id == "EMO_MX_RATE":
            base = kpi.goal * (0.99 + 0.005 * station_bias)
        if kpi.id == "INJURY_COUNT":
            base = (kpi.goal / 7.0) * (0.9 + 0.2 * station_bias)

        # Noise scale relative to goal (scaled for SUM KPIs so weekly aggregation is sane)
        ref = (kpi.goal / 7.0) if kpi.agg == "sum" else kpi.goal
        noise = max(0.01, abs(ref) * 0.10)
        if kpi.id in ("OTS_RATE", "MEL_RATE", "MEL_CX_RATE"):
            noise = max(0.005, kpi.goal * 0.25)
        if kpi.id == "EMO_MX_RATE":
            noise = 0.4
        if kpi.id == "INJURY_COUNT":
            noise = 0.9

        self.daily_root_causes.setdefault(station, {}).setdefault(kpi.id, {})

        def record_cause(day: date, label: str) -> None:
            # Prefer a specific label if multiple events overlap
            if day not in self.daily_root_causes[station][kpi.id]:
                self.daily_root_causes[station][kpi.id][day] = label

        points: List[Tuple[date, float]] = []

        # Curated, deterministic demo events to ensure Wheeler signals trigger.
        # Events are defined relative to the end of the series so the dashboard windows show signals.
        region = REGION_BY_STATION.get(station, "UNKNOWN")

        # Short shift ensures daily window (last 30d) has a clear phase change.
        shift_start = days - 14
        shift_len = 10
        # Longer shift ensures weekly window (last 53w) shows sustained change (run rule).
        weekly_shift_start = days - (7 * 12)
        weekly_shift_len = 7 * 10
        # A “spike week” forces at least one weekly point to stand out.
        spike_week_start = days - (7 * 3)
        spike_week_len = 7
        spike_day = days - 3

        def in_scope(*, scope: str, target_region: Optional[str] = None) -> bool:
            if scope == "company":
                return True
            if scope == "region":
                return bool(target_region and region == target_region)
            return True

        # (kpi_id -> (shift_delta, spike_delta, shift_cause, spike_cause))
        demo_map: Dict[str, tuple[float, float, str, str]] = {
            "OTP_MX_RATE": (0.18, 0.45, "Company: holiday ops disruption", f"{station}: parts shortage"),
            "MX_EXTREME_DELAY_RATE": (0.10, 0.35, "Region: weather-driven tail swaps", f"{station}: AOG event"),
            "MEL_RATE": (0.04, 0.12, "Company: deferred maintenance backlog", f"{station}: MEL deferral surge"),
            "MEL_CX_RATE": (0.01, 0.03, "Region: vendor recovery delays", f"{station}: MEL cancellations cluster"),
            "FAULT_RATE": (0.06, 0.18, "Company: reliability regression", f"{station}: recurring write-up"),
            "FINDING_RATE": (0.25, 0.65, "Region: heavy-check findings", f"{station}: inspection campaign"),
            "OTS_RATE": (0.010, 0.030, "Company: staffing mix change", f"{station}: overtime surge"),
            "PREMIUM_PAY_RATE": (0.8, 2.2, "Company: premium coverage", f"{station}: staffing shortfall"),
            "INJURY_COUNT": (0.7, 2.5, "Company: safety stand-down", f"{station}: localized injury spike"),
        }

        # EMO is “higher is better”, so invert the shift/spike direction.
        if kpi.id == "EMO_MX_RATE":
            demo_map[kpi.id] = (-1.2, -2.8, "Company: hangar system outage", f"{station}: tooling downtime")

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

            # Apply a longer shift to create sustained weekly signals (run rule).
            if kpi.id in demo_map and weekly_shift_start <= i < (weekly_shift_start + weekly_shift_len):
                shift_delta, _spike_delta, shift_cause, _spike_cause = demo_map[kpi.id]
                scope = "region" if kpi.id in ("MX_EXTREME_DELAY_RATE", "MEL_CX_RATE", "FINDING_RATE") else "company"
                target_region = "SOUTH_CENTRAL" if scope == "region" else None
                if in_scope(scope=scope, target_region=target_region):
                    val = val + (shift_delta * 0.6)
                    record_cause(d, shift_cause)

            # Apply curated short shift window to drive daily phase changes in the last 30 days.
            if kpi.id in demo_map and shift_start <= i < (shift_start + shift_len):
                shift_delta, _spike_delta, shift_cause, _spike_cause = demo_map[kpi.id]
                # Region-scoped for a subset of KPIs; otherwise company-wide.
                scope = "region" if kpi.id in ("MX_EXTREME_DELAY_RATE", "MEL_CX_RATE", "FINDING_RATE") else "company"
                target_region = "SOUTH_CENTRAL" if scope == "region" else None
                if in_scope(scope=scope, target_region=target_region):
                    val = val + shift_delta
                    record_cause(d, shift_cause)

            # Apply a spike across an entire week to create a visible weekly outlier.
            if kpi.id in demo_map and spike_week_start <= i < (spike_week_start + spike_week_len):
                _shift_delta, spike_delta, _shift_cause, _spike_cause = demo_map[kpi.id]
                # Keep this slightly smaller than the single-day spike so both are distinct.
                val = val + (spike_delta * 0.35)

            # Apply a hard spike to drive Rule #1 beyond NPL near the end.
            if kpi.id in demo_map and i == spike_day and (station in ("DAL", "PHX") or kpi.id in ("OTP_MX_RATE", "EMO_MX_RATE")):
                _shift_delta, spike_delta, _shift_cause, spike_cause = demo_map[kpi.id]
                val = val + spike_delta
                record_cause(d, spike_cause)

            # injury counts as integers
            if kpi.id == "INJURY_COUNT":
                val = max(0.0, round(val))

            points.append((d, float(val)))

        return points

    def get_kpis(self) -> List[KPIDef]:
        self.ensure_seeded()
        return list(self.kpis.values())

    def get_weekly_series(self, *, station: str, weeks: int = 53, summary_level: str = "station") -> Dict[str, KPISeries]:
        self.ensure_seeded()
        if station not in self.daily:
            raise KeyError(f"Unknown station: {station}")

        scope_stations = _stations_for_summary_level(self.stations, station=station, summary_level=summary_level)

        out: Dict[str, KPISeries] = {}
        for kpi_id, kpi in self.kpis.items():
            # Build weekly buckets per station and then roll up if requested.
            weekly_by_station: Dict[str, List[Tuple[date, float]]] = {}
            for st in scope_stations:
                daily = self.daily[st][kpi_id]
                weekly_by_station[st] = _aggregate_to_weeks(daily=daily, agg=kpi.agg)

            baseline_weeks = [wk for wk, _ in weekly_by_station[scope_stations[0]]]
            # keep last (weeks + 53) so YoY comparisons available
            baseline_weeks = baseline_weeks[-(weeks + 53) :]
            values_by_station = {st: {wk: v for wk, v in weekly_by_station[st]} for st in scope_stations}

            weekly_points: List[Tuple[date, float]] = []
            for wk in baseline_weeks:
                vals = [values_by_station[st].get(wk) for st in scope_stations]
                vals_f = [float(v) for v in vals if v is not None]
                if not vals_f:
                    continue
                weekly_points.append((wk, _aggregate_values(vals_f, agg=kpi.agg)))

            weekly_points = weekly_points[-(weeks + 53) :]
            current = weekly_points[-weeks:]
            prev_year = weekly_points[:weeks] if len(weekly_points) >= (2 * weeks) else []

            yoy_values: List[Optional[float]] = []
            yoy_deltas: List[Optional[float]] = []
            t_values: List[str] = []
            values: List[float] = []
            for idx, (wk, v) in enumerate(current):
                yoy_v = None
                yoy_d = None
                if prev_year and idx < len(prev_year):
                    yoy_v = prev_year[idx][1]
                    yoy_d = v - yoy_v
                t_values.append(wk.isoformat())
                values.append(float(v))
                yoy_values.append(_round(yoy_v, kpi.decimals) if yoy_v is not None else None)
                yoy_deltas.append(_round(yoy_d, kpi.decimals) if yoy_d is not None else None)

            pts, last_limits = _build_metric_points(
                t_values=t_values,
                values=values,
                yoy_values=yoy_values,
                yoy_deltas=yoy_deltas,
                decimals=kpi.decimals,
                clamp_lcl_at_zero=True,
                min_baseline=20,
            )

            vals = values or [0.0]
            mean = sum(vals) / len(vals) if vals else 0.0
            past_value = vals[-1] if vals else 0.0
            prev_value = vals[-2] if len(vals) >= 2 else past_value
            past_delta = past_value - prev_value
            # Wheeler: treat a detected phase change as a meaningful signal (even if the last phase is now stable).
            max_phase = max((p.phase_number or 1) for p in pts) if pts else 1
            last_pt = pts[-1] if pts else None
            if last_pt and last_pt.signal_state == "critical":
                series_state: SignalState = "critical"
            elif max_phase > 1:
                series_state = "warning"
            else:
                series_state = wheeler_signal_state(vals, last_limits)
            out[kpi_id] = KPISeries(
                kpi=kpi,
                points=pts,
                mean=float(_round(mean, kpi.decimals) or 0.0),
                past_value=float(_round(past_value, kpi.decimals) or 0.0),
                past_delta=float(_round(past_delta, kpi.decimals) or 0.0),
                signal_state=series_state,
                npl_cl=float(_round(last_limits.cl, kpi.decimals) or 0.0),
                npl_ucl=float(_round(last_limits.ucl, kpi.decimals) or 0.0),
                npl_lcl=float(_round(last_limits.lcl, kpi.decimals) or 0.0),
                npl_sigma=float(_round(last_limits.sigma, kpi.decimals) or 0.0),
                npl_mr_bar=float(_round(last_limits.mr_bar, kpi.decimals) or 0.0),
            )

        return out

    def get_daily_series(self, *, station: str, days: int = 30, summary_level: str = "station") -> Dict[str, KPISeries]:
        self.ensure_seeded()
        if station not in self.daily:
            raise KeyError(f"Unknown station: {station}")

        scope_stations = _stations_for_summary_level(self.stations, station=station, summary_level=summary_level)

        out: Dict[str, KPISeries] = {}
        for kpi_id, kpi in self.kpis.items():
            # Build daily points per station and then roll up if requested.
            baseline_days = [d for d, _ in self.daily[scope_stations[0]][kpi_id]]
            baseline_days = baseline_days[-395:]  # preserve YoY lookup range

            values_by_station = {st: {d: v for d, v in self.daily[st][kpi_id]} for st in scope_stations}
            daily_series: List[Tuple[date, float]] = []
            for d in baseline_days:
                vals = [values_by_station[st].get(d) for st in scope_stations]
                vals_f = [float(v) for v in vals if v is not None]
                if not vals_f:
                    continue
                daily_series.append((d, _aggregate_values(vals_f, agg=kpi.agg)))

            current = daily_series[-days:]

            # YoY for daily: compare to same day last year (approx 365 days earlier)
            lookup = {d: v for d, v in daily_series}
            yoy_values: List[Optional[float]] = []
            yoy_deltas: List[Optional[float]] = []
            t_values: List[str] = []
            values: List[float] = []
            for d, v in current:
                prev_d = d - timedelta(days=365)
                yoy_v = lookup.get(prev_d)
                yoy_d = (v - yoy_v) if yoy_v is not None else None
                t_values.append(d.isoformat())
                values.append(float(v))
                yoy_values.append(_round(yoy_v, kpi.decimals) if yoy_v is not None else None)
                yoy_deltas.append(_round(yoy_d, kpi.decimals) if yoy_d is not None else None)

            pts, last_limits = _build_metric_points(
                t_values=t_values,
                values=values,
                yoy_values=yoy_values,
                yoy_deltas=yoy_deltas,
                decimals=kpi.decimals,
                clamp_lcl_at_zero=True,
                min_baseline=min(20, max(5, len(values))),
            )

            vals = values or [0.0]
            mean = sum(vals) / len(vals) if vals else 0.0
            past_value = vals[-1] if vals else 0.0
            prev_value = vals[-2] if len(vals) >= 2 else past_value
            past_delta = past_value - prev_value
            max_phase = max((p.phase_number or 1) for p in pts) if pts else 1
            last_pt = pts[-1] if pts else None
            if last_pt and last_pt.signal_state == "critical":
                series_state: SignalState = "critical"
            elif max_phase > 1:
                series_state = "warning"
            else:
                series_state = wheeler_signal_state(vals, last_limits)
            out[kpi_id] = KPISeries(
                kpi=kpi,
                points=pts,
                mean=float(_round(mean, kpi.decimals) or 0.0),
                past_value=float(_round(past_value, kpi.decimals) or 0.0),
                past_delta=float(_round(past_delta, kpi.decimals) or 0.0),
                signal_state=series_state,
                npl_cl=float(_round(last_limits.cl, kpi.decimals) or 0.0),
                npl_ucl=float(_round(last_limits.ucl, kpi.decimals) or 0.0),
                npl_lcl=float(_round(last_limits.lcl, kpi.decimals) or 0.0),
                npl_sigma=float(_round(last_limits.sigma, kpi.decimals) or 0.0),
                npl_mr_bar=float(_round(last_limits.mr_bar, kpi.decimals) or 0.0),
            )

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
