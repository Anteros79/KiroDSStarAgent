"""Wheeler XmR (Individuals) natural process limits utilities.

Ported and simplified from the offline SPC dashboard reference implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Literal, Sequence, Tuple

SignalState = Literal["none", "warning", "critical"]


@dataclass(frozen=True)
class XmRLimits:
    cl: float
    mr_bar: float
    sigma: float
    ucl: float
    lcl: float
    two_sigma_upper: float
    two_sigma_lower: float


@dataclass(frozen=True)
class XmRPhase:
    """A contiguous SPC phase with fixed XmR limits."""

    start_index: int
    end_index: int
    phase_number: int
    limits: XmRLimits


def _to_list(values: Iterable[float]) -> List[float]:
    return [float(v) for v in values]


def calculate_xmr_limits(values: Sequence[float], *, clamp_lcl_at_zero: bool = True) -> XmRLimits:
    """Compute Individuals-chart limits using Wheeler's XmR constants.

    For an Individuals chart:
    - moving ranges are |x[i] - x[i-1]|
    - mr_bar is the mean moving range
    - sigma ≈ mr_bar / 1.128  (d2 for n=2)
    - natural process limits: cl ± 2.66 * mr_bar
    - 2-sigma guard band: cl ± 2 * sigma
    """
    xs = _to_list(values)
    if not xs:
        return XmRLimits(
            cl=0.0,
            mr_bar=0.0,
            sigma=0.0,
            ucl=0.0,
            lcl=0.0,
            two_sigma_upper=0.0,
            two_sigma_lower=0.0,
        )

    cl = sum(xs) / len(xs)
    if len(xs) < 2:
        mr_bar = 0.0
    else:
        mrs = [abs(xs[i] - xs[i - 1]) for i in range(1, len(xs))]
        mr_bar = (sum(mrs) / len(mrs)) if mrs else 0.0

    sigma = (mr_bar / 1.128) if mr_bar > 0 else 0.0
    ucl = cl + 2.66 * mr_bar
    lcl = cl - 2.66 * mr_bar
    if clamp_lcl_at_zero:
        lcl = max(0.0, lcl)

    return XmRLimits(
        cl=cl,
        mr_bar=mr_bar,
        sigma=sigma,
        ucl=ucl,
        lcl=lcl,
        two_sigma_upper=cl + 2 * sigma,
        two_sigma_lower=cl - 2 * sigma,
    )


def wheeler_signal_state(
    values: Sequence[float],
    limits: XmRLimits,
    *,
    run_length: int = 7,
) -> SignalState:
    """Evaluate basic Wheeler special-cause rules focusing on the most recent data.

    Implemented:
    - Rule #1: most recent point outside NPL (UCL/LCL) -> critical
    - Rule #2 (modified): 2 of last 3 points beyond 2-sigma band on same side -> warning
    - Rule #4: last `run_length` points all on same side of CL -> warning
    """
    xs = _to_list(values)
    if not xs:
        return "none"

    last = xs[-1]
    if last > limits.ucl or last < limits.lcl:
        return "critical"

    # 2-of-3 beyond 2-sigma, same side
    recent3 = xs[-3:] if len(xs) >= 3 else xs
    if recent3:
        upper = sum(1 for v in recent3 if v >= limits.two_sigma_upper)
        lower = sum(1 for v in recent3 if v <= limits.two_sigma_lower)
        if upper >= 2 or lower >= 2:
            return "warning"

    # Run on one side of CL
    if len(xs) >= run_length:
        recent = xs[-run_length:]
        if all(v > limits.cl for v in recent) or all(v < limits.cl for v in recent):
            return "warning"

    return "none"


def find_phase_end(
    values: Sequence[float],
    *,
    cl: float,
    ucl: float,
    lcl: float,
    std_dev: float,
    run_length: int = 7,
) -> int:
    """Return index where the current phase ends (relative to `values`).

    Matches the reference SPC dashboard behavior:
    - Rule #1: point beyond NPL -> end at point before outlier
    - Rule #2 (modified): 2 of 3 beyond 2-sigma same side -> end before 3-point window
    - Rule #4: 7 consecutive points on one side of CL -> end before run starts
    """
    xs = _to_list(values)
    if not xs:
        return -1

    two_sigma_upper = cl + 2 * std_dev
    two_sigma_lower = cl - 2 * std_dev

    consecutive_above = 0
    consecutive_below = 0
    recent3: List[float] = []

    for i, value in enumerate(xs):
        # Rule #1: point outside control limits
        if value > ucl or value < lcl:
            return i - 1

        # Rule #4: run on one side
        if value > cl:
            consecutive_above += 1
            consecutive_below = 0
        elif value < cl:
            consecutive_below += 1
            consecutive_above = 0

        if consecutive_above >= run_length or consecutive_below >= run_length:
            return i - run_length

        # Rule #2: 2-of-3 beyond 2-sigma on same side
        recent3.append(value)
        if len(recent3) > 3:
            recent3.pop(0)
        if len(recent3) == 3:
            upper = sum(1 for v in recent3 if v >= two_sigma_upper)
            lower = sum(1 for v in recent3 if v <= two_sigma_lower)
            if upper >= 2 or lower >= 2:
                return i - len(recent3)

    return len(xs) - 1


def detect_xmr_phases(
    values: Sequence[float],
    *,
    min_baseline: int = 20,
    clamp_lcl_at_zero: bool = True,
    run_length: int = 7,
) -> Tuple[List[XmRPhase], List[XmRLimits]]:
    """Detect phases and compute per-point XmR limits.

    Algorithm (reference dashboard):
    1) Establish a baseline (minimum 20 points, or all remaining points)
    2) Compute baseline limits
    3) Scan forward for a Wheeler signal; when found, start a new phase at the signal point
    4) Recompute final phase limits from the entire phase segment
    """
    xs = _to_list(values)
    if len(xs) < 2:
        limits = calculate_xmr_limits(xs, clamp_lcl_at_zero=clamp_lcl_at_zero)
        return [XmRPhase(0, max(0, len(xs) - 1), 1, limits)], [limits for _ in xs]

    phases: List[XmRPhase] = []
    limits_by_index: List[XmRLimits] = [calculate_xmr_limits(xs[:1], clamp_lcl_at_zero=clamp_lcl_at_zero)] * len(xs)

    current_start = 0
    phase_number = 1

    while current_start < len(xs):
        baseline_end = min(current_start + max(1, int(min_baseline)), len(xs))
        baseline_values = xs[current_start:baseline_end]
        if not baseline_values:
            break

        # Baseline limits for signal scanning
        baseline_limits = calculate_xmr_limits(baseline_values, clamp_lcl_at_zero=clamp_lcl_at_zero)
        baseline_std_dev = (baseline_limits.mr_bar / 1.128) if baseline_limits.mr_bar > 0 else 0.001

        if baseline_end >= len(xs):
            phase_end = len(xs) - 1
        else:
            remaining = xs[baseline_end:]
            signal_offset = find_phase_end(
                remaining,
                cl=baseline_limits.cl,
                ucl=baseline_limits.ucl,
                lcl=baseline_limits.lcl,
                std_dev=baseline_std_dev,
                run_length=run_length,
            )
            phase_end = baseline_end + signal_offset
            phase_end = max(current_start, min(phase_end, len(xs) - 1))

        phase_values = xs[current_start : phase_end + 1]
        phase_limits = calculate_xmr_limits(phase_values, clamp_lcl_at_zero=clamp_lcl_at_zero)

        phases.append(
            XmRPhase(
                start_index=current_start,
                end_index=phase_end,
                phase_number=phase_number,
                limits=phase_limits,
            )
        )
        for idx in range(current_start, phase_end + 1):
            limits_by_index[idx] = phase_limits

        current_start = phase_end + 1
        phase_number += 1

    return phases, limits_by_index
