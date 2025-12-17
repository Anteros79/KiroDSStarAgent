"""Tech Ops diagnostic tests for explaining KPI signal spikes.

These tests are deterministic and operate on the in-memory TechOpsStore time series.
They are meant to be run sequentially (without repeats) until the question is answered.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

from src.data.techops_metrics import TechOpsStore
from src.spc.wheeler import XmRLimits, calculate_xmr_limits, detect_xmr_phases

Window = Literal["weekly", "daily"]
SummaryLevel = Literal["station", "region", "company"]


@dataclass(frozen=True)
class TechOpsContext:
    kpi_id: str
    station: str
    window: Window
    point_t: Optional[str] = None
    summary_level: SummaryLevel = "station"


def _get_series(store: TechOpsStore, ctx: TechOpsContext):
    if ctx.window == "weekly":
        series_map = store.get_weekly_series(station=ctx.station, weeks=53, summary_level=ctx.summary_level)
    else:
        series_map = store.get_daily_series(station=ctx.station, days=30, summary_level=ctx.summary_level)
    return series_map[ctx.kpi_id]


def _selected_index(ts: List[str], point_t: Optional[str]) -> int:
    if point_t and point_t in ts:
        return ts.index(point_t)
    return max(0, len(ts) - 1)


def build_test_plan(ctx: TechOpsContext) -> List[str]:
    # Ordered list: fast characterization first, then comparisons, then narrative.
    return [
        "signal_characterization",
        "yoy_seasonality",
        "cross_station",
        "pre_post_shift",
        "final_summary",
    ]


def run_test(*, store: TechOpsStore, ctx: TechOpsContext, test_name: str) -> Dict[str, Any]:
    s = _get_series(store, ctx)
    t_list = [p.t for p in s.points]
    values = [float(p.value) for p in s.points]

    idx = _selected_index(t_list, ctx.point_t)
    selected_t = t_list[idx] if t_list else None
    selected_v = values[idx] if values else None

    phases, limits_by_idx = detect_xmr_phases(values, min_baseline=min(20, max(5, len(values))), clamp_lcl_at_zero=True)
    limits: XmRLimits = limits_by_idx[-1] if limits_by_idx else calculate_xmr_limits(values, clamp_lcl_at_zero=True)
    selected_point = s.points[idx] if s.points else None
    selected_limits = limits_by_idx[idx] if idx < len(limits_by_idx) else limits
    known_cause = store.get_root_cause(
        kpi_id=ctx.kpi_id,
        station=ctx.station,
        window=str(ctx.window),
        t=selected_t,
        summary_level=str(getattr(ctx, "summary_level", "station")),
    )

    if test_name == "signal_characterization":
        # Rule #1 vs near-limit: simple classification based on selected point.
        beyond = bool(selected_v is not None and (selected_v > selected_limits.ucl or selected_v < selected_limits.lcl))
        phase_num = getattr(selected_point, "phase_number", None) if selected_point else None
        stage_change = False
        if idx > 0 and phase_num is not None and s.points:
            prev_phase = getattr(s.points[idx - 1], "phase_number", phase_num)
            stage_change = bool(prev_phase != phase_num)

        mr = abs(values[idx] - values[idx - 1]) if idx > 0 and values else None
        mr_ucl = None
        mr_signal = None
        try:
            ph = next((p for p in phases if p.start_index <= idx <= p.end_index), None)
            if ph and idx > 0:
                mr_start = max(1, ph.start_index + 1)
                mr_end = ph.end_index
                mrs = [abs(values[i] - values[i - 1]) for i in range(mr_start, mr_end + 1)]
                mr_bar = (sum(mrs) / len(mrs)) if mrs else 0.0
                mr_ucl = mr_bar * 3.268
                mr_signal = bool(mr is not None and mr_ucl is not None and mr > mr_ucl)
        except Exception:
            pass

        return {
            "test": test_name,
            "selected_t": selected_t,
            "selected_value": selected_v,
            "ucl": selected_limits.ucl,
            "lcl": selected_limits.lcl,
            "cl": selected_limits.cl,
            "mr": mr,
            "phase_number": phase_num,
            "stage_change": stage_change,
            "mr_ucl": mr_ucl,
            "mr_signal": mr_signal,
            "known_demo_root_cause": known_cause,
            "finding": "selected point beyond NPL (Rule #1)" if beyond else "selected point within NPL (no Rule #1)",
        }

    if test_name == "yoy_seasonality":
        p = s.points[idx] if s.points else None
        return {
            "test": test_name,
            "selected_t": selected_t,
            "selected_value": selected_v,
            "yoy_value": getattr(p, "yoy_value", None) if p else None,
            "yoy_delta": getattr(p, "yoy_delta", None) if p else None,
            "finding": "YoY delta computed for selected point (if available).",
        }

    if test_name == "cross_station":
        # Compare selected point value across peer stations for same date/week.
        # In region/company rollups, compare the user's station vs other stations to diagnose locality.
        peers = [st for st in ("DAL", "PHX", "HOU") if st != ctx.station]
        peer_values: Dict[str, Optional[float]] = {}
        for st in peers:
            peer_ctx = TechOpsContext(kpi_id=ctx.kpi_id, station=st, window=ctx.window, point_t=selected_t, summary_level="station")
            peer_s = _get_series(store, peer_ctx)
            peer_t = [p.t for p in peer_s.points]
            peer_v = [float(p.value) for p in peer_s.points]
            pidx = _selected_index(peer_t, selected_t)
            peer_values[st] = peer_v[pidx] if peer_v else None

        vals = [v for v in peer_values.values() if v is not None]
        peer_mean = (sum(vals) / len(vals)) if vals else None
        return {
            "test": test_name,
            "selected_t": selected_t,
            "selected_value": selected_v,
            "peer_values": peer_values,
            "peer_mean": peer_mean,
            "finding": "Compare station vs peers to isolate local vs systemic movement.",
        }

    if test_name == "pre_post_shift":
        # Compare recent window vs prior window (simple mean shift).
        n = 7 if ctx.window == "daily" else 5
        if len(values) < (2 * n):
            return {
                "test": test_name,
                "selected_t": selected_t,
                "finding": f"Not enough points for {n}+{n} pre/post comparison.",
            }
        pre = values[-(2 * n) : -n]
        post = values[-n:]
        pre_mean = sum(pre) / len(pre)
        post_mean = sum(post) / len(post)
        return {
            "test": test_name,
            "window_n": n,
            "pre_mean": pre_mean,
            "post_mean": post_mean,
            "delta": post_mean - pre_mean,
            "finding": "Mean-shift check (recent vs prior) to see if this is a one-off spike or sustained shift.",
        }

    if test_name == "final_summary":
        # Lightweight deterministic summary (LLM may add narrative later).
        beyond = bool(selected_v is not None and (selected_v > selected_limits.ucl or selected_v < selected_limits.lcl))
        return {
            "test": test_name,
            "selected_t": selected_t,
            "selected_value": selected_v,
            "ucl": selected_limits.ucl,
            "lcl": selected_limits.lcl,
            "cl": selected_limits.cl,
            "known_demo_root_cause": known_cause,
            "finding": (
                "Likely special-cause spike (Rule #1) at selected point." if beyond else "No Rule #1 spike at selected point."
            ),
        }

    raise ValueError(f"Unknown test_name: {test_name}")


def format_test_result(result: Dict[str, Any]) -> str:
    test_name = str(result.get("test", "test"))
    lines = [f"TEST: {test_name}", f"FINDING: {result.get('finding', '')}".strip()]

    # Show a compact key/value snapshot (stable ordering)
    keys = [
        "selected_t",
        "selected_value",
        "phase_number",
        "stage_change",
        "cl",
        "ucl",
        "lcl",
        "mr",
        "mr_ucl",
        "mr_signal",
        "yoy_value",
        "yoy_delta",
        "peer_mean",
        "peer_values",
        "pre_mean",
        "post_mean",
        "delta",
        "window_n",
        "known_demo_root_cause",
    ]
    for k in keys:
        if k in result and result[k] is not None:
            lines.append(f"- {k}: {result[k]}")

    return "\n".join(lines).strip()
