"""Demo scenarios for Tech Ops KPI investigations.

These scenarios provide realistic data storytelling for demonstrations,
with correlated measures, common fields (aircraft, date, station), and
compelling narratives that showcase the DS-STAR analysis capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Any


@dataclass
class DemoScenario:
    """A pre-built demo scenario with realistic data story."""
    id: str
    title: str
    station: str
    primary_kpi: str
    window: str  # 'weekly' or 'daily'
    narrative: str
    root_cause: str
    expected_findings: List[str]
    related_kpis: List[str]
    evidence_points: List[str]
    recommended_actions: List[str]
    # For demo: specific date to investigate
    point_t: Optional[str] = None
    # Confidence levels for each diagnostic test
    diagnostic_confidences: Dict[str, float] = field(default_factory=dict)


# Pre-built demo scenarios for tomorrow's presentation
DEMO_SCENARIOS: List[DemoScenario] = [
    DemoScenario(
        id="phx_parts_shortage",
        title="PHX Parts Shortage Impact on OTP",
        station="PHX",
        primary_kpi="OTP_MX_RATE",
        window="weekly",
        narrative="""
Phoenix station experienced a significant spike in maintenance-related delays 
over the past 3 weeks. Initial analysis shows OTP MX Rate jumped from 2.1% to 
3.8%, breaching the upper control limit. Cross-station comparison reveals this 
is isolated to PHX - peer stations DAL and HOU remain stable at ~2.0%.

The root cause traces to a parts availability issue: critical brake assembly 
components (P/N 2615400-5) experienced a 12-day backorder from the primary 
vendor. This created a cascade effect where aircraft requiring brake service 
were held AOG, forcing tail swaps and crew reassignments.

The MEL Rate also spiked (+0.08) as technicians deferred non-critical items 
to prioritize brake-related work. Premium Pay Rate increased 2.3% due to 
overtime required for expedited repairs once parts arrived.
        """.strip(),
        root_cause="Parts shortage: Brake assembly P/N 2615400-5 backorder (12 days)",
        expected_findings=[
            "Rule #1 violation: OTP MX Rate 3.8% exceeds UCL of 3.2%",
            "Stage change detected at week -3 (new phase established)",
            "Cross-station: PHX isolated - DAL 2.0%, HOU 2.1% stable",
            "YoY delta: +1.2% vs same period last year",
            "Pre/post shift: +1.7% mean increase over 5-week window",
        ],
        related_kpis=["MEL_RATE", "PREMIUM_PAY_RATE", "FAULT_RATE"],
        evidence_points=[
            "Parts requisition log shows 47 backorders for P/N 2615400-5",
            "AOG report: 8 aircraft held for brake service",
            "Crew scheduling: 23 tail swaps attributed to PHX MX holds",
        ],
        recommended_actions=[
            "Establish secondary vendor for critical brake components",
            "Increase safety stock for high-turnover parts at PHX",
            "Review predictive maintenance schedule for brake assemblies",
            "Coordinate with procurement on vendor lead time monitoring",
        ],
        diagnostic_confidences={
            "signal_characterization": 0.92,
            "yoy_seasonality": 0.78,
            "cross_station": 0.95,
            "pre_post_shift": 0.88,
            "final_summary": 0.91,
        },
    ),
    DemoScenario(
        id="dal_weather_cascade",
        title="DAL Weather Cascade Effect on Dispatch",
        station="DAL",
        primary_kpi="MX_EXTREME_DELAY_RATE",
        window="daily",
        narrative="""
Dallas experienced severe thunderstorms over a 4-day period, triggering a 
cascade of maintenance-related extreme delays. The MX Extreme Delay Rate 
spiked to 1.8% (vs normal 0.9%), with 15 flights exceeding 3-hour delays 
due to maintenance holds.

The weather event itself caused initial ground stops, but the downstream 
effect on maintenance was significant: aircraft arriving late missed 
scheduled overnight checks, creating a backlog. Technicians worked extended 
shifts to clear the queue, but several aircraft required MEL deferrals to 
maintain schedule integrity.

Cross-station analysis shows HOU (same region) experienced similar but 
less severe impact (+0.4%), while PHX remained unaffected. This confirms 
the regional weather pattern as the primary driver.
        """.strip(),
        root_cause="Weather cascade: 4-day thunderstorm event disrupted overnight maintenance schedule",
        expected_findings=[
            "Rule #1 violation: Extreme Delay Rate 1.8% exceeds UCL of 1.4%",
            "MR signal detected: High point-to-point volatility",
            "Cross-station: Regional pattern - HOU +0.4%, PHX stable",
            "YoY delta: +0.6% vs same period (no weather event last year)",
            "Pre/post shift: Sustained elevation over 4-day window",
        ],
        related_kpis=["OTP_MX_RATE", "MEL_RATE", "PREMIUM_PAY_RATE"],
        evidence_points=[
            "Weather log: 47 ground stop hours over 4-day period",
            "Overnight check backlog: 12 aircraft deferred",
            "MEL log: 28 new deferrals during event window",
        ],
        recommended_actions=[
            "Develop weather contingency staffing protocol",
            "Pre-position mobile maintenance teams during forecast events",
            "Establish priority queue for post-weather check clearing",
            "Review MEL deferral limits during extended disruptions",
        ],
        diagnostic_confidences={
            "signal_characterization": 0.89,
            "yoy_seasonality": 0.72,
            "cross_station": 0.94,
            "pre_post_shift": 0.85,
            "final_summary": 0.88,
        },
    ),
    DemoScenario(
        id="company_reliability_regression",
        title="Fleet-Wide Fault Rate Regression",
        station="DAL",
        primary_kpi="FAULT_RATE",
        window="weekly",
        narrative="""
A company-wide increase in Fault Rate has been detected across all stations, 
suggesting a systemic issue rather than localized problem. The rate increased 
from 0.48 to 0.72 over 8 weeks, with all three stations (DAL, PHX, HOU) 
showing similar trajectories.

Investigation reveals the timing correlates with a fleet-wide software update 
to the Engine Indication and Crew Alerting System (EICAS). The update 
introduced more sensitive fault detection thresholds, resulting in increased 
write-ups for conditions previously below reporting threshold.

This is a "good news" signal - the system is now catching issues earlier. 
However, the maintenance workload has increased, and the Finding Rate has 
also risen as technicians investigate the new fault alerts.
        """.strip(),
        root_cause="EICAS software update: Lowered fault detection thresholds (intentional)",
        expected_findings=[
            "Stage change: New baseline established at week -8",
            "Cross-station: All stations show parallel increase (systemic)",
            "YoY delta: +0.24 vs same period (pre-update baseline)",
            "Pre/post shift: +0.24 mean increase, sustained",
            "No Rule #1 violation in current phase (new normal)",
        ],
        related_kpis=["FINDING_RATE", "MEL_RATE", "OTP_MX_RATE"],
        evidence_points=[
            "EICAS update log: Version 4.2.1 deployed fleet-wide week -8",
            "Fault category analysis: 73% increase in 'minor' severity faults",
            "No increase in 'critical' or 'major' fault categories",
        ],
        recommended_actions=[
            "Update control limits to reflect new detection baseline",
            "Communicate to maintenance teams: increased faults expected",
            "Monitor workload impact on technician overtime",
            "Review fault-to-finding conversion rate for efficiency",
        ],
        diagnostic_confidences={
            "signal_characterization": 0.95,
            "yoy_seasonality": 0.65,
            "cross_station": 0.98,
            "pre_post_shift": 0.92,
            "final_summary": 0.94,
        },
    ),
]


def get_demo_scenario(scenario_id: str) -> Optional[DemoScenario]:
    """Get a specific demo scenario by ID."""
    for scenario in DEMO_SCENARIOS:
        if scenario.id == scenario_id:
            return scenario
    return None


def get_scenarios_for_station(station: str) -> List[DemoScenario]:
    """Get all demo scenarios for a specific station."""
    return [s for s in DEMO_SCENARIOS if s.station == station]


def get_scenario_summary() -> List[Dict[str, Any]]:
    """Get a summary of all available demo scenarios."""
    return [
        {
            "id": s.id,
            "title": s.title,
            "station": s.station,
            "primary_kpi": s.primary_kpi,
            "window": s.window,
            "root_cause": s.root_cause,
        }
        for s in DEMO_SCENARIOS
    ]


def apply_scenario_diagnostics(
    diagnostics: List[Dict[str, Any]],
    scenario: DemoScenario,
) -> List[Dict[str, Any]]:
    """Enhance diagnostic results with scenario-specific confidence levels."""
    enhanced = []
    for diag in diagnostics:
        test_name = diag.get("test", diag.get("name", ""))
        confidence = scenario.diagnostic_confidences.get(test_name, 0.75)
        enhanced.append({
            **diag,
            "confidence": confidence,
            "status": "completed",
        })
    return enhanced
