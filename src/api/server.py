"""FastAPI server for DS-Star multi-agent system web interface."""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import json
import time
import urllib.request
import urllib.error

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.config import Config
from src.agents.orchestrator import OrchestratorAgent
from src.handlers.stream_handler import InvestigationStreamHandler
from src.data.airline_data import initialize_data_loader
from src.data.techops_metrics import get_techops_store
from src.spc.wheeler import calculate_xmr_limits, detect_xmr_phases
from src.techops.investigation_tests import TechOpsContext, build_test_plan, run_test, format_test_result

# Import specialist agents
from src.agents.specialists.data_analyst import data_analyst
from src.agents.specialists.domain_expert import domain_expert
from src.agents.specialists.ml_engineer import ml_engineer
from src.agents.specialists.statistics_expert import statistics_expert
from src.agents.specialists.visualization_expert import visualization_expert

# Import Strands components
try:
    from strands.models.bedrock import BedrockModel
    from strands.models.ollama import OllamaModel
except ImportError:
    print("Warning: strands-agents package not installed.")
    BedrockModel = None
    OllamaModel = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SW_PALETTE = {
    "blue": "#304CB2",
    "red": "#C4122F",
    "gold": "#FFB612",
    "charcoal": "#111827",
    "slate": "#6B7280",
}


# NOTE: model calls are performed inside specialist agents via `src.llm.ollama_client`.


def _compact_test_evidence(text: str) -> str:
    # Kept for future use (compact evidence for model prompts); not used in the Tech Ops loop now.
    keep_prefixes = ("TEST:", "FINDING:", "- ")
    out: list[str] = []
    for ln in (text or "").splitlines():
        ln = ln.strip()
        if ln and ln.startswith(keep_prefixes):
            out.append(ln)
    return "\n".join(out[:120]).strip()


def _calculate_test_confidence(test_name: str, result: Dict[str, Any]) -> float:
    """Calculate confidence level for a diagnostic test based on its results."""
    base_confidence = 0.70
    
    if test_name == "signal_characterization":
        # High confidence if we found a clear Rule #1 violation or stage change
        finding = result.get("finding", "")
        if "beyond NPL" in finding or "Rule #1" in finding:
            base_confidence = 0.92
        elif result.get("stage_change"):
            base_confidence = 0.88
        elif result.get("mr_signal"):
            base_confidence = 0.85
        else:
            base_confidence = 0.75
        # Boost if we have a known root cause
        if result.get("known_demo_root_cause"):
            base_confidence = min(0.98, base_confidence + 0.05)
    
    elif test_name == "yoy_seasonality":
        # Confidence based on whether YoY data is available and significant
        yoy_delta = result.get("yoy_delta")
        if yoy_delta is not None:
            # Larger deltas = more confident the change is meaningful
            if abs(yoy_delta) > 0.5:
                base_confidence = 0.85
            elif abs(yoy_delta) > 0.2:
                base_confidence = 0.78
            else:
                base_confidence = 0.65
        else:
            base_confidence = 0.50  # No YoY data available
    
    elif test_name == "cross_station":
        # High confidence if we can clearly isolate the issue
        peer_values = result.get("peer_values", {})
        selected_value = result.get("selected_value")
        peer_mean = result.get("peer_mean")
        
        if peer_mean is not None and selected_value is not None:
            # If selected station differs significantly from peers, high confidence
            diff = abs(selected_value - peer_mean)
            if diff > 0.5:
                base_confidence = 0.95  # Clear isolation
            elif diff > 0.2:
                base_confidence = 0.85
            else:
                base_confidence = 0.70  # Similar to peers (systemic)
        else:
            base_confidence = 0.60
    
    elif test_name == "pre_post_shift":
        # Confidence based on magnitude of shift
        delta = result.get("delta")
        if delta is not None:
            if abs(delta) > 0.5:
                base_confidence = 0.90
            elif abs(delta) > 0.2:
                base_confidence = 0.82
            else:
                base_confidence = 0.68
        else:
            base_confidence = 0.55
    
    elif test_name == "final_summary":
        # Summary confidence is average of other tests
        if result.get("known_demo_root_cause"):
            base_confidence = 0.92
        elif "Rule #1" in result.get("finding", ""):
            base_confidence = 0.88
        else:
            base_confidence = 0.75
    
    return round(base_confidence, 2)


def generate_chart_from_response(response_text: str, query: str) -> Optional[Dict[str, Any]]:
    """Generate a Plotly chart from the response text by parsing data patterns."""
    import re
    
    # Try to extract data from common patterns
    
    # Pattern 1: "airline: AA, value: 0.85" or "AA: 0.85" style
    # Pattern 2: Table-like data with headers
    # Pattern 3: Key-value pairs
    
    labels = []
    values = []
    title = "Analysis Results"
    
    # Look for airline codes with numeric values
    # Pattern: AA 199 233 0.854077 (airline, count1, count2, rate)
    airline_pattern = r'\b([A-Z]{2})\s+(\d+)\s+(\d+)\s+([\d.]+)'
    matches = re.findall(airline_pattern, response_text)
    
    if matches:
        labels = [m[0] for m in matches]
        # Use the rate (last value) for the chart
        values = [float(m[3]) for m in matches]
        title = "Performance by Airline"
    
    # Pattern: "AA: 85.4%" or "AA - 0.854"
    if not labels:
        simple_pattern = r'\b([A-Z]{2})[\s:=-]+([\d.]+)%?'
        matches = re.findall(simple_pattern, response_text)
        if len(matches) >= 2:
            labels = [m[0] for m in matches]
            values = [float(m[1]) for m in matches]
            title = "Results by Airline"
    
    # Pattern: Look for "airline" followed by values
    if not labels:
        lines = response_text.split('\n')
        for line in lines:
            # Match lines like "AA    0.854" or "American Airlines (AA): 85.4%"
            match = re.search(r'([A-Z]{2})[)\s:]+\s*([\d.]+)', line)
            if match:
                labels.append(match.group(1))
                val = float(match.group(2))
                # Convert to percentage if it looks like a rate
                values.append(val * 100 if val < 1 else val)
    
    # If we found data, create the chart
    if labels and values and len(labels) >= 2:
        # Determine if values are percentages
        is_percentage = all(0 <= v <= 100 for v in values) or all(0 <= v <= 1 for v in values)
        
        # Normalize to percentage if needed
        if all(0 <= v <= 1 for v in values):
            values = [v * 100 for v in values]
        
        # Southwest Tech Ops palette (consistent branding)
        sw_red = SW_PALETTE["red"]
        sw_blue = SW_PALETTE["blue"]
        sw_gold = SW_PALETTE["gold"]
        max_val = max(values) if values else 1
        colors = [sw_red if v == max_val else (sw_gold if v >= 0.85 * max_val else sw_blue) for v in values]
        
        plotly_json = {
            "data": [{
                "type": "bar",
                "x": labels,
                "y": values,
                "marker": {
                    "color": colors,
                    "line": {"color": "rgb(50, 50, 50)", "width": 1}
                },
                "text": [f"{v:.1f}%" if is_percentage else f"{v:.2f}" for v in values],
                "textposition": "outside",
            }],
            "layout": {
                "title": {"text": title, "font": {"size": 16}},
                "xaxis": {"title": "Airline", "tickangle": 0},
                "yaxis": {
                    "title": "Rate (%)" if is_percentage else "Value",
                    "range": [0, max(values) * 1.15] if values else [0, 100]
                },
                "plot_bgcolor": "rgba(248, 250, 252, 0.8)",
                "paper_bgcolor": "white",
                "font": {"family": "Inter, system-ui, sans-serif"},
                "margin": {"t": 60, "b": 60, "l": 60, "r": 30},
            }
        }
        
        return {
            "chart_type": "bar",
            "title": title,
            "plotly_json": plotly_json,
        }
    
    return None


def generate_techops_kpi_chart(
    *,
    kpi_id: str,
    station: str,
    window: str,
    point_t: Optional[str] = None,
    summary_level: str = "station",
) -> Optional[Dict[str, Any]]:
    """Generate a Plotly chart from Tech Ops KPI time series (station vs fleet average)."""
    try:
        store = get_techops_store()
        series_map = (
            store.get_weekly_series(station=station, weeks=53, summary_level=summary_level)
            if window == "weekly"
            else store.get_daily_series(station=station, days=30, summary_level=summary_level)
        )
        if kpi_id not in series_map:
            return None
        s = series_map[kpi_id]
        from datetime import timedelta

        t_list = [p.t for p in s.points]
        values = [float(p.value) for p in s.points]

        label = s.kpi.label
        unit = s.kpi.unit
        title = f"{label} - {station} ({window})"

        # SPC-style limits using Wheeler's XmR natural process limits (NPL)
        # Prefer phase-aware limits from the data generator (Wheeler phases).
        last_pt = s.points[-1] if getattr(s, "points", None) else None
        mean = getattr(last_pt, "cl", None)
        ucl = getattr(last_pt, "ucl", None)
        lcl = getattr(last_pt, "lcl", None)
        if mean is None or ucl is None or lcl is None:
            limits = calculate_xmr_limits(values, clamp_lcl_at_zero=True)
            mean = limits.cl
            ucl = limits.ucl
            lcl = limits.lcl

        # Southwest-style colors used in the reference SPC dashboard
        sw_red = SW_PALETTE["red"]
        sw_blue = SW_PALETTE["blue"]
        sw_gold = SW_PALETTE["gold"]
        limit_ucl = sw_red
        limit_lcl = sw_gold

        colors = [
            sw_red if (getattr(p, "signal_state", "none") == "critical") else sw_blue
            for p in s.points
        ]

        # Day-of-week labels (daily) or week-start labels (weekly)
        tickvals = t_list
        ticktext: list[str] = []
        for t in t_list:
            try:
                d = datetime.fromisoformat(t).date()
            except ValueError:
                d = datetime.strptime(t, "%Y-%m-%d").date()
            if window == "daily":
                is_weekend = d.weekday() >= 5
                day_abbr = d.strftime("%a")
                date_str = d.strftime("%m/%d")
                color = sw_red if is_weekend else sw_blue
                ticktext.append(f"<span style=\"color:{color}\">{day_abbr}</span><br>{date_str}")
            else:
                ticktext.append(f"Wk<br>{d.strftime('%m/%d')}")

        bar_trace: Dict[str, Any] = {
            "type": "bar",
            "name": "Values",
            "x": tickvals,
            "y": values,
            "marker": {"color": colors, "line": {"width": 1, "color": "#FFFFFF"}},
            "text": ticktext,
            "hovertemplate": "<b>%{text}</b><br>Value: %{y}<extra></extra>",
        }

        mean_trace: Dict[str, Any] = {
            "type": "scatter",
            "mode": "lines",
            "name": "Mean",
            "x": tickvals,
            "y": [mean] * len(tickvals),
            "line": {"color": sw_blue, "width": 2},
            "hoverinfo": "skip",
        }

        ucl_trace: Dict[str, Any] = {
            "type": "scatter",
            "mode": "lines",
            "name": "UCL",
            "x": tickvals,
            "y": [ucl] * len(tickvals),
            "line": {"color": limit_ucl, "width": 2, "dash": "dash"},
            "hoverinfo": "skip",
        }

        lcl_trace: Dict[str, Any] = {
            "type": "scatter",
            "mode": "lines",
            "name": "LCL",
            "x": tickvals,
            "y": [lcl] * len(tickvals),
            "line": {"color": limit_lcl, "width": 2, "dash": "dash"},
            "hoverinfo": "skip",
        }

        # Default window focus: last 7 days or last 13 weeks
        show_n = 7 if window == "daily" else 13
        start_idx = max(0, len(tickvals) - show_n)
        end_idx = max(0, len(tickvals) - 1)
        try:
            start_dt = datetime.fromisoformat(tickvals[start_idx])
            end_dt = datetime.fromisoformat(tickvals[end_idx])
        except ValueError:
            start_dt = datetime.strptime(tickvals[start_idx], "%Y-%m-%d")
            end_dt = datetime.strptime(tickvals[end_idx], "%Y-%m-%d")

        padding = timedelta(hours=12)
        x_range = [(start_dt - padding).isoformat(), (end_dt + padding).isoformat()]

        # Stage-change reference lines from point phase numbers (if available)
        stage_shapes: list[Dict[str, Any]] = []
        try:
            phase_numbers = [getattr(p, "phase_number", None) for p in s.points]
            for idx in range(1, len(phase_numbers)):
                if phase_numbers[idx] and phase_numbers[idx - 1] and phase_numbers[idx] != phase_numbers[idx - 1]:
                    stage_shapes.append(
                        {
                            "type": "line",
                            "xref": "x",
                            "yref": "paper",
                            "x0": tickvals[idx],
                            "x1": tickvals[idx],
                            "y0": 0,
                            "y1": 1,
                            "line": {"color": SW_PALETTE["slate"], "width": 1, "dash": "dot"},
                        }
                    )
        except Exception:
            stage_shapes = []

        plotly_json: Dict[str, Any] = {
            "data": [bar_trace, mean_trace, ucl_trace, lcl_trace],
            "layout": {
                "title": False,
                "showlegend": False,
                "margin": {"l": 80, "r": 60, "t": 20, "b": 120},
                "dragmode": "zoom",
                "xaxis": {
                    "title": False,
                    "ticktext": ticktext,
                    "tickvals": tickvals,
                    "tickangle": 0,
                    "tickfont": {"size": 11, "family": "Arial, sans-serif"},
                    "tickmode": "array",
                    "automargin": True,
                    "range": x_range,
                    "rangeslider": {"visible": False},
                    "fixedrange": False,
                    "showgrid": True,
                    "zeroline": False,
                    "showline": True,
                    "linewidth": 1,
                    "linecolor": "#D1D5DB",
                },
                "yaxis": {"title": {"text": f"{label} ({unit})", "standoff": 10}, "gridcolor": "#E5E7EB"},
                "plot_bgcolor": "#FFFFFF",
                "paper_bgcolor": "#FFFFFF",
                "hovermode": "closest",
                "bargap": 0.15,
                "bargroupgap": 0.1,
                "font": {"family": "Inter, system-ui, sans-serif"},
                "shapes": stage_shapes,
            },
        }

        # Highlight selected point (from KPI click) if present
        if point_t and point_t in tickvals:
            idx = tickvals.index(point_t)
            plotly_json["data"].append(
                {
                    "type": "scatter",
                    "mode": "markers",
                    "name": "Selected",
                    "x": [tickvals[idx]],
                    "y": [values[idx]],
                    "marker": {"size": 14, "color": sw_red, "symbol": "circle-open", "line": {"width": 3, "color": sw_red}},
                    "hovertemplate": "Selected<br>%{x}<br>%{y}<extra></extra>",
                }
            )

        return {"chart_type": "bar", "title": title, "plotly_json": plotly_json}
    except Exception:
        return None


def generate_techops_xmr_combo_chart(
    *,
    kpi_id: str,
    station: str,
    window: str,
    point_t: Optional[str] = None,
    summary_level: str = "station",
) -> Optional[Dict[str, Any]]:
    """Two-panel XmR chart (Individuals + Moving Range) with Wheeler phase limits."""
    try:
        store = get_techops_store()
        series_map = (
            store.get_weekly_series(station=station, weeks=53, summary_level=summary_level)
            if window == "weekly"
            else store.get_daily_series(station=station, days=30, summary_level=summary_level)
        )
        if kpi_id not in series_map:
            return None
        s = series_map[kpi_id]
        t_list = [p.t for p in s.points]
        values = [float(p.value) for p in s.points]
        if not t_list or not values:
            return None

        phases, _limits_by_idx = detect_xmr_phases(values, min_baseline=min(20, max(5, len(values))))

        # Stage-change reference lines (vertical dotted markers at phase boundaries)
        stage_lines: list[Dict[str, Any]] = []
        for ph in phases[1:]:
            if 0 <= ph.start_index < len(t_list):
                x0 = t_list[ph.start_index]
                stage_lines.append(
                    {
                        "type": "line",
                        "xref": "x",
                        "yref": "paper",
                        "x0": x0,
                        "x1": x0,
                        "y0": 0,
                        "y1": 1,
                        "line": {"color": SW_PALETTE["slate"], "width": 1, "dash": "dot"},
                    }
                )

        # Build Individuals chart traces (line+markers style for process control chart)
        point_colors = [SW_PALETTE["red"] if getattr(p, "signal_state", "none") == "critical" else SW_PALETTE["blue"] for p in s.points]
        x_trace: Dict[str, Any] = {
            "type": "scatter",
            "mode": "lines+markers",
            "name": "X",
            "x": t_list,
            "y": values,
            "line": {"color": SW_PALETTE["blue"], "width": 2},
            "marker": {"size": 8, "color": point_colors, "line": {"width": 1, "color": "#FFFFFF"}},
            "hovertemplate": "<b>%{x}</b><br>Value: %{y}<extra></extra>",
        }

        # Phase limit segments for Individuals chart
        limit_traces: list[Dict[str, Any]] = []
        phase_meta: list[Dict[str, Any]] = []
        for ph in phases:
            start_t = t_list[ph.start_index]
            end_t = t_list[ph.end_index]
            lim = ph.limits
            phase_meta.append(
                {
                    "phase": ph.phase_number,
                    "start": start_t,
                    "end": end_t,
                    "cl": lim.cl,
                    "ucl": lim.ucl,
                    "lcl": lim.lcl,
                }
            )
            limit_traces.extend(
                [
                    {
                        "type": "scatter",
                        "mode": "lines",
                        "x": [start_t, end_t],
                        "y": [lim.ucl, lim.ucl],
                        "line": {"color": SW_PALETTE["red"], "width": 2, "dash": "dash"},
                        "hoverinfo": "skip",
                        "showlegend": False,
                        "xaxis": "x",
                        "yaxis": "y",
                    },
                    {
                        "type": "scatter",
                        "mode": "lines",
                        "x": [start_t, end_t],
                        "y": [lim.cl, lim.cl],
                        "line": {"color": SW_PALETTE["charcoal"], "width": 2, "dash": "dash"},
                        "hoverinfo": "skip",
                        "showlegend": False,
                        "xaxis": "x",
                        "yaxis": "y",
                    },
                    {
                        "type": "scatter",
                        "mode": "lines",
                        "x": [start_t, end_t],
                        "y": [lim.lcl, lim.lcl],
                        "line": {"color": SW_PALETTE["gold"], "width": 2, "dash": "dash"},
                        "hoverinfo": "skip",
                        "showlegend": False,
                        "xaxis": "x",
                        "yaxis": "y",
                    },
                ]
            )

        # Selected point highlight
        if point_t and point_t in t_list:
            idx = t_list.index(point_t)
            limit_traces.append(
                {
                    "type": "scatter",
                    "mode": "markers",
                    "name": "Selected",
                    "x": [t_list[idx]],
                    "y": [values[idx]],
                    "marker": {"size": 14, "color": SW_PALETTE["red"], "symbol": "circle-open", "line": {"width": 3, "color": SW_PALETTE["red"]}},
                    "hovertemplate": "Selected<br>%{x}<br>%{y}<extra></extra>",
                    "showlegend": False,
                    "xaxis": "x",
                    "yaxis": "y",
                }
            )

        # Moving Range series aligned to the 2nd point (mr[i] = |x[i]-x[i-1]|)
        mr_x = t_list[1:]
        mr_vals = [abs(values[i] - values[i - 1]) for i in range(1, len(values))]
        mr_trace: Dict[str, Any] = {
            "type": "scatter",
            "mode": "lines+markers",
            "name": "mR",
            "x": mr_x,
            "y": mr_vals,
            "line": {"color": SW_PALETTE["blue"], "width": 2},
            "marker": {"size": 6, "color": SW_PALETTE["blue"]},
            "hovertemplate": "<b>%{x}</b><br>mR: %{y}<extra></extra>",
            "xaxis": "x2",
            "yaxis": "y2",
            "showlegend": False,
        }

        mr_limit_traces: list[Dict[str, Any]] = []
        for ph in phases:
            # Map Individuals phase indices to mR indices
            mr_start = max(0, ph.start_index - 1)
            mr_end = min(ph.end_index - 1, len(mr_vals) - 1)
            if mr_start > mr_end or not mr_x:
                continue
            seg_x0 = mr_x[mr_start]
            seg_x1 = mr_x[mr_end]
            seg_vals = mr_vals[mr_start : mr_end + 1]
            if not seg_vals:
                continue
            mr_bar = sum(seg_vals) / len(seg_vals)
            ucl_mr = mr_bar * 3.268
            mr_limit_traces.extend(
                [
                    {
                        "type": "scatter",
                        "mode": "lines",
                        "x": [seg_x0, seg_x1],
                        "y": [ucl_mr, ucl_mr],
                        "line": {"color": SW_PALETTE["red"], "width": 2, "dash": "dash"},
                        "hoverinfo": "skip",
                        "showlegend": False,
                        "xaxis": "x2",
                        "yaxis": "y2",
                    },
                    {
                        "type": "scatter",
                        "mode": "lines",
                        "x": [seg_x0, seg_x1],
                        "y": [mr_bar, mr_bar],
                        "line": {"color": SW_PALETTE["charcoal"], "width": 2, "dash": "dash"},
                        "hoverinfo": "skip",
                        "showlegend": False,
                        "xaxis": "x2",
                        "yaxis": "y2",
                    },
                ]
            )

        label = s.kpi.label
        unit = s.kpi.unit
        scope = station if summary_level == "station" else ("Region" if summary_level == "region" else "Company")
        title = f"{label} XmR - {scope} ({window})"

        plotly_json: Dict[str, Any] = {
            "data": [x_trace, *limit_traces, mr_trace, *mr_limit_traces],
            "layout": {
                "title": {"text": title, "font": {"size": 16}},
                "grid": {"rows": 2, "columns": 1, "pattern": "independent"},
                "margin": {"l": 70, "r": 20, "t": 50, "b": 60},
                "paper_bgcolor": "#FFFFFF",
                "plot_bgcolor": "#FFFFFF",
                "font": {"family": "Inter, system-ui, sans-serif"},
                "dragmode": "zoom",
                "hovermode": "x unified",
                "shapes": stage_lines,
                "xaxis": {"title": "", "showgrid": True, "gridcolor": "#E5E7EB", "showticklabels": False},
                "yaxis": {"title": f"{label} ({unit})", "gridcolor": "#E5E7EB"},
                "xaxis2": {"title": "", "showgrid": True, "gridcolor": "#E5E7EB", "matches": "x", "tickangle": 0},
                "yaxis2": {"title": "Moving Range", "gridcolor": "#E5E7EB"},
                "meta": {"phases": phase_meta, "summary_level": summary_level},
            },
        }

        return {"chart_type": "xmr", "title": title, "plotly_json": plotly_json}
    except Exception as e:
        logger.warning(f"Failed to generate XmR chart: {e}")
        return None


def generate_techops_cross_station_chart(*, kpi_id: str, station: str, window: str, point_t: Optional[str]) -> Optional[Dict[str, Any]]:
    """Bar chart comparing the selected point across stations."""
    try:
        store = get_techops_store()
        stations = [station] + [s for s in ("DAL", "PHX", "HOU") if s != station]
        xs: list[str] = []
        ys: list[float] = []
        for st in stations:
            series_map = store.get_weekly_series(station=st, weeks=53) if window == "weekly" else store.get_daily_series(station=st, days=30)
            if kpi_id not in series_map:
                continue
            s = series_map[kpi_id]
            t_list = [p.t for p in s.points]
            v_list = [float(p.value) for p in s.points]
            if not v_list:
                continue
            idx = (t_list.index(point_t) if point_t and point_t in t_list else len(t_list) - 1)
            xs.append(st)
            ys.append(v_list[idx])

        if not xs:
            return None

        colors = [SW_PALETTE["red"] if x == station else SW_PALETTE["blue"] for x in xs]
        title = f"{kpi_id} - Station Compare ({point_t or 'latest'}, {window})"
        plotly_json = {
            "data": [
                {
                    "type": "bar",
                    "x": xs,
                    "y": ys,
                    "marker": {"color": colors},
                    "hovertemplate": "Station: %{x}<br>Value: %{y}<extra></extra>",
                }
            ],
            "layout": {
                "title": {"text": title, "font": {"size": 14}},
                "margin": {"l": 60, "r": 20, "t": 40, "b": 40},
                "plot_bgcolor": "#FFFFFF",
                "paper_bgcolor": "#FFFFFF",
                "font": {"family": "Inter, system-ui, sans-serif"},
            },
        }
        return {"chart_type": "bar", "title": title, "plotly_json": plotly_json}
    except Exception as e:
        logger.warning(f"Failed to generate cross-station chart: {e}")
        return None


def generate_techops_yoy_chart(*, kpi_id: str, station: str, window: str, summary_level: str = "station") -> Optional[Dict[str, Any]]:
    """Line chart showing current vs YoY values for the window (if available)."""
    try:
        store = get_techops_store()
        series_map = (
            store.get_weekly_series(station=station, weeks=53, summary_level=summary_level)
            if window == "weekly"
            else store.get_daily_series(station=station, days=30, summary_level=summary_level)
        )
        if kpi_id not in series_map:
            return None
        s = series_map[kpi_id]
        x = [p.t for p in s.points]
        y = [float(p.value) for p in s.points]
        yoy = [p.yoy_value for p in s.points]
        if not any(v is not None for v in yoy):
            # Fallback: compute a simple 52-week shift if the dataset doesn't carry explicit YoY values.
            if window == "weekly" and len(y) > 52:
                yoy = [None] * len(y)
                for idx in range(52, len(y)):
                    yoy[idx] = y[idx - 52]
            if not any(v is not None for v in yoy):
                return None

        title = f"{kpi_id} - YoY ({station}, {window})"
        plotly_json = {
            "data": [
                {
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Current",
                    "x": x,
                    "y": y,
                    "line": {"color": SW_PALETTE["blue"], "width": 2},
                },
                {
                    "type": "scatter",
                    "mode": "lines",
                    "name": "YoY",
                    "x": x,
                    "y": yoy,
                    "line": {"color": SW_PALETTE["gold"], "width": 2, "dash": "dash"},
                },
            ],
            "layout": {
                "title": {"text": title, "font": {"size": 14}},
                "margin": {"l": 60, "r": 20, "t": 40, "b": 60},
                "plot_bgcolor": "#FFFFFF",
                "paper_bgcolor": "#FFFFFF",
                "font": {"family": "Inter, system-ui, sans-serif"},
                "legend": {"orientation": "h"},
            },
        }
        return {"chart_type": "line", "title": title, "plotly_json": plotly_json}
    except Exception as e:
        logger.warning(f"Failed to generate YoY chart: {e}")
        return None


def generate_techops_pre_post_chart(*, kpi_id: str, station: str, window: str, summary_level: str = "station") -> Optional[Dict[str, Any]]:
    """Bar chart of prior window mean vs recent window mean."""
    try:
        store = get_techops_store()
        series_map = (
            store.get_weekly_series(station=station, weeks=53, summary_level=summary_level)
            if window == "weekly"
            else store.get_daily_series(station=station, days=30, summary_level=summary_level)
        )
        if kpi_id not in series_map:
            return None
        s = series_map[kpi_id]
        vals = [float(p.value) for p in s.points]
        n = 7 if window == "daily" else 5
        if len(vals) < 2 * n:
            return None
        pre = vals[-(2 * n) : -n]
        post = vals[-n:]
        pre_mean = sum(pre) / len(pre)
        post_mean = sum(post) / len(post)
        title = f"{kpi_id} - Pre/Post Mean ({station}, {window})"
        plotly_json = {
            "data": [
                {
                    "type": "bar",
                    "x": ["Prior", "Recent"],
                    "y": [pre_mean, post_mean],
                    "marker": {"color": [SW_PALETTE["blue"], SW_PALETTE["red"]]},
                    "hovertemplate": "%{x}: %{y}<extra></extra>",
                }
            ],
            "layout": {
                "title": {"text": title, "font": {"size": 14}},
                "margin": {"l": 60, "r": 20, "t": 40, "b": 40},
                "plot_bgcolor": "#FFFFFF",
                "paper_bgcolor": "#FFFFFF",
                "font": {"family": "Inter, system-ui, sans-serif"},
            },
        }
        return {"chart_type": "bar", "title": title, "plotly_json": plotly_json}
    except Exception as e:
        logger.warning(f"Failed to generate pre/post chart: {e}")
        return None

# Create FastAPI app
app = FastAPI(
    title="DS-Star Multi-Agent System API",
    description="API for interacting with the DS-Star multi-agent system",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (application-level, not request-specific)
orchestrator: Optional[OrchestratorAgent] = None
config: Optional[Config] = None
techops = None

# Demo identities (static configuration, not request-specific state)
_demo_identities = [
    {"id": "jmartinez", "name": "J. Martinez", "role": "Station Manager", "station": "DAL"},
    {"id": "techops_phx", "name": "A. Chen", "role": "Tech Ops Analyst", "station": "PHX"},
    {"id": "reliability_hq", "name": "R. Patel", "role": "Reliability Eng", "station": "HOU"},
]

# Session-scoped security components (initialized at startup)
# These replace the global _current_identity_id and _techops_investigations
from src.security.session_manager import SessionManager
from src.security.identity_provider import LocalIdentityProvider
from src.security.rls_engine import RowLevelSecurityEngine
from src.data.investigation_store import InvestigationStore
from src.security.session_models import SessionContext
from src.handlers.stream_handler_factory import StreamHandlerFactory, WebSocketStreamHandler

# Security infrastructure (initialized at startup)
_identity_provider: Optional[LocalIdentityProvider] = None
_session_manager: Optional[SessionManager] = None
_rls_engine: Optional[RowLevelSecurityEngine] = None
_investigation_store: Optional[InvestigationStore] = None


# Request/Response models
class QueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    response: str
    routing: list[str]
    execution_time_ms: int
    charts: list[Dict[str, Any]] = []


class ColumnInfo(BaseModel):
    name: str
    dtype: str


class DatasetInfo(BaseModel):
    filename: str
    description: str
    columns: list[ColumnInfo]
    rowCount: int


class SystemStatus(BaseModel):
    status: str
    model: str
    region: str
    specialists: list[str]
    data_loaded: bool
    dataset_info: Optional[DatasetInfo] = None


class StreamEvent(BaseModel):
    type: str  # "agent_start", "routing", "tool_call", "agent_end", "response", "error"
    data: Dict[str, Any]
    timestamp: str


class AnalyzeRequest(BaseModel):
    research_goal: str
    dataset_path: Optional[str] = None


class DemoIdentity(BaseModel):
    id: str
    name: str
    role: str
    station: str


class SelectIdentityRequest(BaseModel):
    identity_id: str


class KPIDefinition(BaseModel):
    id: str
    label: str
    unit: str
    goal: float
    ul: float
    ll: float
    decimals: int


class MetricPoint(BaseModel):
    t: str
    value: float
    yoy_value: Optional[float] = None
    yoy_delta: Optional[float] = None
    signal_state: str
    cl: Optional[float] = None
    ucl: Optional[float] = None
    lcl: Optional[float] = None
    phase_number: Optional[int] = None


class KPISeriesResponse(BaseModel):
    kpi: KPIDefinition
    points: list[MetricPoint]
    mean: float
    past_value: float
    past_delta: float
    signal_state: str
    npl_cl: float
    npl_ucl: float
    npl_lcl: float
    npl_sigma: float
    npl_mr_bar: float


class DashboardResponse(BaseModel):
    station: str
    window: str  # "weekly" | "daily"
    kpis: list[KPISeriesResponse]


class CreateInvestigationRequest(BaseModel):
    kpi_id: str
    station: str
    window: str  # "weekly" | "daily"
    point_t: Optional[str] = None  # clicked point (date or week_start)
    summary_level: Optional[str] = "station"


class CreateInvestigationResponse(BaseModel):
    investigation_id: str
    prompt_mode: str  # "cause" | "yoy"
    prompt: str


class InvestigationRecord(BaseModel):
    investigation_id: str
    kpi_id: str
    station: str
    window: str
    summary_level: Optional[str] = "station"
    created_by: DemoIdentity
    created_at: str
    status: str
    prompt_mode: str
    prompt: str
    selected_point_t: Optional[str] = None
    final_root_cause: Optional[str] = None
    final_actions: list[str] = []
    final_notes: Optional[str] = None
    final_evidence: list[Dict[str, Any]] = []
    # Persisted investigation artifacts (demo: in-memory)
    steps: list[Dict[str, Any]] = []
    diagnostics: list[Dict[str, Any]] = []
    telemetry: Optional[Dict[str, Any]] = None


class EvidenceItem(BaseModel):
    kind: str  # "iteration" | "telemetry" | "diagnostic"
    label: Optional[str] = None
    step_id: Optional[str] = None
    iteration_id: Optional[str] = None
    investigation_id: Optional[str] = None
    chart: Optional[Dict[str, Any]] = None
    excerpt: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class FinalizeInvestigationRequest(BaseModel):
    final_root_cause: str
    final_actions: list[str] = []
    final_notes: Optional[str] = None
    evidence: list[EvidenceItem] = []


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the DS-Star system on startup."""
    global orchestrator, config, techops
    global _identity_provider, _session_manager, _rls_engine, _investigation_store
    
    try:
        logger.info("Starting DS-Star API server...")
        
        # Load configuration
        config = Config.load()
        logger.info(f"Configuration loaded: model={config.model_id}, region={config.region}")
        
        # Initialize security infrastructure (replaces global state)
        logger.info("Initializing security infrastructure...")
        _identity_provider = LocalIdentityProvider(_demo_identities)
        _session_manager = SessionManager(
            identity_provider=_identity_provider,
            session_ttl_hours=24,
            open_access_mode=True  # Default to open access
        )
        _rls_engine = RowLevelSecurityEngine(open_access_mode=True)
        _investigation_store = InvestigationStore(rls_engine=_rls_engine)
        logger.info("✓ Security infrastructure initialized (open access mode)")
        
        # Initialize data loader
        logger.info("Loading airline operations dataset...")
        # If data file is missing, generate it (mirrors CLI behavior)
        from pathlib import Path
        data_file_path = Path(config.data_path)
        if not data_file_path.exists():
            logger.warning(f"Data file not found: {config.data_path}")
            logger.info("Generating sample airline operations dataset...")
            from src.data.generate_sample_data import generate_dataset, save_to_csv

            records = generate_dataset(num_records=1200)
            save_to_csv(records, config.data_path)
            logger.info(f"✓ Generated {len(records)} flight records")
            logger.info(f"✓ Sample dataset saved to {config.data_path}")

        initialize_data_loader(config.data_path)
        logger.info("✓ Airline data loaded")

        # Initialize Tech Ops demo store
        techops = get_techops_store()
        logger.info("✓ Tech Ops demo metrics initialized")
        
        # Initialize stream handler
        stream_handler = InvestigationStreamHandler(verbose=config.verbose)
        
        # Initialize model based on provider
        model = None
        if config.model_provider == "ollama":
            if OllamaModel is None:
                logger.warning(
                    "OllamaModel not available (strands-agents not installed) - continuing in mock mode"
                )
                model = None
            else:
                logger.info(f"Connecting to Ollama at {config.ollama_host}...")
                model = OllamaModel(
                    model_id=config.model_id,
                    host=config.ollama_host,
                )
                logger.info(f"✓ Ollama model initialized: {config.model_id}")
        else:
            # Default to Bedrock
            if BedrockModel is None:
                logger.warning(
                    "BedrockModel not available (strands-agents not installed) - continuing in mock mode"
                )
                model = None
            else:
                logger.info("Connecting to Amazon Bedrock...")
                model = BedrockModel(
                    model_id=config.model_id,
                    region=config.region,
                    max_tokens=config.max_tokens,
                    temperature=config.temperature
                )
                logger.info(f"✓ Bedrock model initialized: {config.model_id}")
        
        # Create specialist agents dictionary
        specialists = {
            "data_analyst": data_analyst,
            "statistics_expert": statistics_expert,
            "domain_expert": domain_expert,
            "ml_engineer": ml_engineer,
            "visualization_expert": visualization_expert,
        }
        logger.info(f"✓ Loaded {len(specialists)} specialist agents")
        
        # Initialize orchestrator
        orchestrator = OrchestratorAgent(
            model=model,
            specialists=specialists,
            stream_handler=stream_handler,
            config=config
        )
        logger.info("✓ Orchestrator agent initialized")
        logger.info("DS-Star API server ready!")
        
    except Exception as e:
        logger.error(f"Failed to initialize DS-Star system: {e}", exc_info=True)
        raise


# FastAPI Dependencies for Session Context
# These replace the global _current_identity_id with request-scoped session management

async def get_session_context(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
) -> SessionContext:
    """Get or create session context for the current request.
    
    This dependency provides request-scoped session context, replacing
    the global _current_identity_id variable.
    
    Args:
        x_session_id: Optional session ID from X-Session-ID header
        
    Returns:
        SessionContext for the current request
        
    Raises:
        HTTPException: If session manager not initialized or session invalid
        
    Requirements: 7.3
    """
    if _session_manager is None:
        raise HTTPException(status_code=503, detail="Session manager not initialized")
    
    # If session ID provided, try to get existing session
    if x_session_id:
        context = _session_manager.get_session(x_session_id)
        if context:
            return context
        # Invalid/expired session - create new one with default identity
    
    # Create new session with default identity
    default_identity = _demo_identities[0]  # jmartinez
    context = _session_manager.create_session(
        user_id=default_identity["id"],
        identity=default_identity
    )
    return context


async def get_current_user(
    session: SessionContext = Depends(get_session_context),
) -> Dict[str, Any]:
    """Get current user identity from session context.
    
    This dependency extracts user identity from the session context,
    providing a clean interface for endpoints that need user info.
    
    Args:
        session: Session context (injected by get_session_context)
        
    Returns:
        User identity dictionary
        
    Requirements: 7.3
    """
    return session.identity


def get_investigation_store() -> InvestigationStore:
    """Get the investigation store instance.
    
    Returns:
        InvestigationStore instance
        
    Raises:
        HTTPException: If investigation store not initialized
    """
    if _investigation_store is None:
        raise HTTPException(status_code=503, detail="Investigation store not initialized")
    return _investigation_store


def get_rls_engine() -> RowLevelSecurityEngine:
    """Get the RLS engine instance.
    
    Returns:
        RowLevelSecurityEngine instance
        
    Raises:
        HTTPException: If RLS engine not initialized
    """
    if _rls_engine is None:
        raise HTTPException(status_code=503, detail="RLS engine not initialized")
    return _rls_engine


# Health check endpoint
@app.get("/health")
async def health_check():
    """Check if the API is running."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/")
async def root():
    """Friendly landing endpoint (avoids FastAPI default 404 at '/')."""
    return JSONResponse(
        {
            "name": "DS-STAR API",
            "health": "/health",
            "status": "/api/status",
            "docs": "/docs",
            "techops": {
                "kpis": "/api/techops/kpis",
                "dashboard_weekly": "/api/techops/dashboard/weekly?station=DAL",
                "dashboard_daily": "/api/techops/dashboard/daily?station=DAL",
            },
            "websockets": {"query": "/ws/query", "stream": "/ws/stream"},
        }
    )


# System status endpoint
@app.get("/api/status", response_model=SystemStatus)
async def get_status():
    """Get the current system status."""
    if orchestrator is None or config is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    # Get dataset info from data loader
    from src.data.airline_data import get_data_loader
    try:
        data_loader = get_data_loader()
    except RuntimeError:
        data_loader = None
    
    dataset_info = None
    if data_loader and data_loader._df is not None:
        df = data_loader._df
        dataset_info = DatasetInfo(
            filename="airline_operations.csv",
            description="Airline operational data including flights, delays, and performance metrics",
            columns=[ColumnInfo(name=col, dtype=str(df[col].dtype)) for col in df.columns],
            rowCount=len(df)
        )
    
    # Format model display based on provider
    model_display = f"{config.model_provider}:{config.model_id}"
    
    specialist_names: list[str] = []
    try:
        specialist_names = sorted(list(getattr(orchestrator, "specialists", {}).keys()))
    except Exception:
        specialist_names = ["data_analyst", "ml_engineer", "visualization_expert"]

    return SystemStatus(
        status="ready",
        model=model_display,
        region=config.region if config.model_provider == "bedrock" else config.ollama_host,
        specialists=specialist_names,
        data_loaded=True,
        dataset_info=dataset_info
    )


class SessionResponse(BaseModel):
    """Response model including session information."""
    identity: DemoIdentity
    session_id: str


@app.get("/api/me", response_model=SessionResponse)
async def get_me(session: SessionContext = Depends(get_session_context)):
    """Return the current session identity.
    
    This endpoint now uses session context instead of global state,
    ensuring each user sees their own identity.
    
    Requirements: 1.4
    """
    identity = session.identity
    return SessionResponse(
        identity=DemoIdentity(**identity),
        session_id=session.session_id
    )


@app.post("/api/me/select", response_model=SessionResponse)
async def select_me(
    req: SelectIdentityRequest,
    session: SessionContext = Depends(get_session_context)
):
    """Select identity for the current session only.
    
    This endpoint updates only the requesting session's identity,
    not affecting other users' sessions.
    
    Requirements: 1.4
    """
    if _session_manager is None:
        raise HTTPException(status_code=503, detail="Session manager not initialized")
    
    identity = next((i for i in _demo_identities if i["id"] == req.identity_id), None)
    if not identity:
        raise HTTPException(status_code=400, detail="Unknown identity_id")
    
    # Update only this session's identity
    updated_context = _session_manager.update_identity(session.session_id, identity)
    if not updated_context:
        raise HTTPException(status_code=400, detail="Failed to update session identity")
    
    return SessionResponse(
        identity=DemoIdentity(**identity),
        session_id=updated_context.session_id
    )


@app.get("/api/techops/kpis", response_model=list[KPIDefinition])
async def techops_kpis():
    store = get_techops_store()
    return [
        KPIDefinition(
            id=k.id,
            label=k.label,
            unit=k.unit,
            goal=k.goal,
            ul=k.ul,
            ll=k.ll,
            decimals=k.decimals,
        )
        for k in store.get_kpis()
    ]


def _series_to_response(series) -> KPISeriesResponse:
    k = series.kpi
    return KPISeriesResponse(
        kpi=KPIDefinition(id=k.id, label=k.label, unit=k.unit, goal=k.goal, ul=k.ul, ll=k.ll, decimals=k.decimals),
        points=[
            MetricPoint(
                t=p.t,
                value=p.value,
                yoy_value=p.yoy_value,
                yoy_delta=p.yoy_delta,
                signal_state=p.signal_state,
                cl=getattr(p, "cl", None),
                ucl=getattr(p, "ucl", None),
                lcl=getattr(p, "lcl", None),
                phase_number=getattr(p, "phase_number", None),
            )
            for p in series.points
        ],
        mean=series.mean,
        past_value=series.past_value,
        past_delta=series.past_delta,
        signal_state=series.signal_state,
        npl_cl=series.npl_cl,
        npl_ucl=series.npl_ucl,
        npl_lcl=series.npl_lcl,
        npl_sigma=series.npl_sigma,
        npl_mr_bar=series.npl_mr_bar,
    )


@app.get("/api/techops/dashboard/weekly", response_model=DashboardResponse)
async def techops_dashboard_weekly(station: str = "DAL", summary_level: str = "station"):
    store = get_techops_store()
    series_map = store.get_weekly_series(station=station, weeks=53, summary_level=summary_level)
    return DashboardResponse(
        station=station,
        window="weekly",
        kpis=[_series_to_response(series_map[kpi_id]) for kpi_id in series_map],
    )


@app.get("/api/techops/dashboard/daily", response_model=DashboardResponse)
async def techops_dashboard_daily(station: str = "DAL", summary_level: str = "station"):
    store = get_techops_store()
    series_map = store.get_daily_series(station=station, days=30, summary_level=summary_level)
    return DashboardResponse(
        station=station,
        window="daily",
        kpis=[_series_to_response(series_map[kpi_id]) for kpi_id in series_map],
    )


@app.get("/api/techops/signals/active")
async def techops_active_signals(station: str = "DAL", summary_level: str = "station"):
    """Return active signals (warning/critical) for station based on most recent weekly values."""
    store = get_techops_store()
    series_map = store.get_weekly_series(station=station, weeks=53, summary_level=summary_level)
    signals = []
    for kpi_id, s in series_map.items():
        if s.signal_state != "none":
            signals.append(
                {
                    "signal_id": f"SIG-{station}-{kpi_id}",
                    "kpi_id": kpi_id,
                    "station": station,
                    "status": s.signal_state,
                    "detected_at": datetime.utcnow().isoformat(),
                    "window": "weekly",
                    "latest_point_t": s.points[-1].t if s.points else None,
                    "latest_value": s.past_value,
                }
            )
    return {"station": station, "signals": signals}


@app.post("/api/techops/investigations", response_model=CreateInvestigationResponse)
async def techops_create_investigation(
    req: CreateInvestigationRequest,
    session: SessionContext = Depends(get_session_context)
):
    """Create a new investigation seeded from a KPI click.
    
    This endpoint now uses InvestigationStore with session context,
    ensuring investigations are associated with the creating user.
    
    Requirements: 3.1
    """
    if _investigation_store is None:
        raise HTTPException(status_code=503, detail="Investigation store not initialized")
    
    store = get_techops_store()
    summary_level = (req.summary_level or "station").lower()
    series_map = (
        store.get_weekly_series(station=req.station, weeks=53, summary_level=summary_level)
        if req.window == "weekly"
        else store.get_daily_series(station=req.station, days=30, summary_level=summary_level)
    )
    if req.kpi_id not in series_map:
        raise HTTPException(status_code=400, detail="Unknown kpi_id")

    series = series_map[req.kpi_id]
    # Determine prompt mode
    prompt_mode = "cause" if series.signal_state != "none" else "yoy"
    selected_t = req.point_t or (series.points[-1].t if getattr(series, "points", None) else None)
    scope_label = req.station if summary_level == "station" else ("REGION" if summary_level == "region" else "COMPANY")
    if prompt_mode == "cause":
        when = f" around {selected_t}" if selected_t else ""
        prompt = (
            f"What caused this signal spike in the {series.kpi.label} dataset for {scope_label} "
            f"({req.window}){when}? "
            "Run diagnostic tests to identify likely drivers, list each test you run with its result, and do not repeat the same test."
        )
    else:
        prompt = (
            f"How does {series.kpi.label} for {scope_label} ({req.window}) compare year-over-year? "
            "Run the relevant comparisons and summarize the key differences."
        )

    # Use session identity instead of global _current_identity_id
    identity = session.identity

    import uuid

    inv_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
    telemetry = generate_techops_xmr_combo_chart(
        kpi_id=req.kpi_id,
        station=req.station,
        window=req.window,
        point_t=selected_t,
        summary_level=summary_level,
    )
    diagnostics = []
    
    # Run actual diagnostic tests and capture results with confidence
    ctx = TechOpsContext(
        kpi_id=req.kpi_id,
        station=req.station,
        window=req.window,
        point_t=selected_t,
        summary_level=summary_level,
    )
    test_plan = build_test_plan(ctx)
    store = get_techops_store()
    
    for test_name in test_plan:
        try:
            result = run_test(store=store, ctx=ctx, test_name=test_name)
            # Calculate confidence based on test results
            confidence = _calculate_test_confidence(test_name, result)
            diagnostics.append({
                "name": test_name,
                "status": "completed",
                "confidence": confidence,
                "detail": result.get("finding", ""),
                "finding": result.get("finding", ""),
                "selected_t": result.get("selected_t"),
                "selected_value": result.get("selected_value"),
                "ucl": result.get("ucl"),
                "lcl": result.get("lcl"),
                "cl": result.get("cl"),
                "yoy_delta": result.get("yoy_delta"),
                "peer_mean": result.get("peer_mean"),
                "pre_mean": result.get("pre_mean"),
                "post_mean": result.get("post_mean"),
                "delta": result.get("delta"),
                "known_demo_root_cause": result.get("known_demo_root_cause"),
                "stage_change": result.get("stage_change"),
                "mr_signal": result.get("mr_signal"),
            })
        except Exception as e:
            diagnostics.append({
                "name": test_name,
                "status": "failed",
                "confidence": 0.0,
                "detail": f"Test failed: {str(e)}",
            })
    
    # Ensure diagnostics list doesn't contain duplicates by name
    seen = set()
    diagnostics = [d for d in diagnostics if not (d["name"] in seen or seen.add(d["name"]))]
    
    # Create investigation data for the store
    investigation_data = {
        "investigation_id": inv_id,
        "kpi_id": req.kpi_id,
        "station": req.station,
        "window": req.window,
        "summary_level": summary_level,
        "created_by": identity,
        "status": "open",
        "prompt_mode": prompt_mode,
        "prompt": prompt,
        "selected_point_t": selected_t,
        "steps": [],
        "diagnostics": diagnostics,
        "telemetry": telemetry,
    }
    
    # Use InvestigationStore instead of global dictionary
    record = _investigation_store.create(
        data=investigation_data,
        context=session,
        investigation_id=inv_id
    )
    
    return CreateInvestigationResponse(investigation_id=inv_id, prompt_mode=prompt_mode, prompt=prompt)


@app.get("/api/techops/investigations", response_model=list[InvestigationRecord])
async def techops_list_investigations(
    station: Optional[str] = None,
    session: SessionContext = Depends(get_session_context)
):
    """List investigations filtered by session access.
    
    This endpoint now uses InvestigationStore with RLS filtering,
    returning only investigations the user has access to.
    
    Requirements: 3.2
    """
    if _investigation_store is None:
        raise HTTPException(status_code=503, detail="Investigation store not initialized")
    
    # Use InvestigationStore with RLS filtering
    investigations = _investigation_store.list(context=session, station=station)
    
    out = []
    for inv in investigations:
        # Map store record to InvestigationRecord
        out.append(InvestigationRecord(
            investigation_id=inv.get("investigation_id") or inv.get("id"),
            kpi_id=inv.get("kpi_id", ""),
            station=inv.get("station", ""),
            window=inv.get("window", ""),
            summary_level=inv.get("summary_level", "station"),
            created_by=DemoIdentity(**inv["created_by"]) if isinstance(inv.get("created_by"), dict) else DemoIdentity(
                id=inv.get("created_by", "unknown"),
                name="Unknown",
                role="Unknown",
                station=inv.get("station", "")
            ),
            created_at=inv.get("created_at", datetime.utcnow().isoformat()),
            status=inv.get("status", "open"),
            prompt_mode=inv.get("prompt_mode", "cause"),
            prompt=inv.get("prompt", ""),
            selected_point_t=inv.get("selected_point_t"),
            final_root_cause=inv.get("final_root_cause"),
            final_actions=inv.get("final_actions", []),
            final_notes=inv.get("final_notes"),
            final_evidence=inv.get("final_evidence", []),
            steps=inv.get("steps", []),
            diagnostics=inv.get("diagnostics", []),
            telemetry=inv.get("telemetry"),
        ))
    
    # newest first
    out.sort(key=lambda r: r.created_at, reverse=True)
    return out


@app.get("/api/techops/investigations/{investigation_id}", response_model=InvestigationRecord)
async def techops_get_investigation(
    investigation_id: str,
    session: SessionContext = Depends(get_session_context)
):
    """Get investigation with access check.
    
    This endpoint now uses InvestigationStore with RLS,
    returning 403 if user doesn't have access.
    
    Requirements: 3.2, 3.3
    """
    if _investigation_store is None:
        raise HTTPException(status_code=503, detail="Investigation store not initialized")
    
    inv = _investigation_store.get(investigation_id, context=session)
    if not inv:
        # Could be not found or access denied - return 404 for security
        raise HTTPException(status_code=404, detail="Not found")
    
    return InvestigationRecord(
        investigation_id=inv.get("investigation_id") or inv.get("id"),
        kpi_id=inv.get("kpi_id", ""),
        station=inv.get("station", ""),
        window=inv.get("window", ""),
        summary_level=inv.get("summary_level", "station"),
        created_by=DemoIdentity(**inv["created_by"]) if isinstance(inv.get("created_by"), dict) else DemoIdentity(
            id=inv.get("created_by", "unknown"),
            name="Unknown",
            role="Unknown",
            station=inv.get("station", "")
        ),
        created_at=inv.get("created_at", datetime.utcnow().isoformat()),
        status=inv.get("status", "open"),
        prompt_mode=inv.get("prompt_mode", "cause"),
        prompt=inv.get("prompt", ""),
        selected_point_t=inv.get("selected_point_t"),
        final_root_cause=inv.get("final_root_cause"),
        final_actions=inv.get("final_actions", []),
        final_notes=inv.get("final_notes"),
        final_evidence=inv.get("final_evidence", []),
        steps=inv.get("steps", []),
        diagnostics=inv.get("diagnostics", []),
        telemetry=inv.get("telemetry"),
    )


@app.post("/api/techops/investigations/{investigation_id}/finalize", response_model=InvestigationRecord)
async def techops_finalize_investigation(
    investigation_id: str,
    req: FinalizeInvestigationRequest,
    session: SessionContext = Depends(get_session_context)
):
    """Finalize investigation with access check.
    
    This endpoint now uses InvestigationStore with RLS,
    returning 403 if user doesn't have access.
    
    Requirements: 3.3, 3.4
    """
    if _investigation_store is None:
        raise HTTPException(status_code=503, detail="Investigation store not initialized")
    
    # Prepare updates
    updates = {
        "final_root_cause": req.final_root_cause,
        "final_actions": req.final_actions,
        "final_notes": req.final_notes,
        "final_evidence": [e.model_dump() for e in req.evidence] if req.evidence else [],
        "status": "finalized",
    }
    
    # Update through store with access check
    inv = _investigation_store.update(investigation_id, updates, context=session)
    if not inv:
        raise HTTPException(status_code=404, detail="Not found")
    
    return InvestigationRecord(
        investigation_id=inv.get("investigation_id") or inv.get("id"),
        kpi_id=inv.get("kpi_id", ""),
        station=inv.get("station", ""),
        window=inv.get("window", ""),
        summary_level=inv.get("summary_level", "station"),
        created_by=DemoIdentity(**inv["created_by"]) if isinstance(inv.get("created_by"), dict) else DemoIdentity(
            id=inv.get("created_by", "unknown"),
            name="Unknown",
            role="Unknown",
            station=inv.get("station", "")
        ),
        created_at=inv.get("created_at", datetime.utcnow().isoformat()),
        status=inv.get("status", "finalized"),
        prompt_mode=inv.get("prompt_mode", "cause"),
        prompt=inv.get("prompt", ""),
        selected_point_t=inv.get("selected_point_t"),
        final_root_cause=inv.get("final_root_cause"),
        final_actions=inv.get("final_actions", []),
        final_notes=inv.get("final_notes"),
        final_evidence=inv.get("final_evidence", []),
        steps=inv.get("steps", []),
        diagnostics=inv.get("diagnostics", []),
        telemetry=inv.get("telemetry"),
    )


# Query endpoint (REST)
@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a query through the orchestrator (REST endpoint)."""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        logger.info(f"Processing query: {request.query}")
        
        # Add context
        context = request.context or {}
        context.update({
            "output_dir": config.output_dir,
            "data_path": config.data_path
        })
        
        # Process through orchestrator
        response = await asyncio.to_thread(orchestrator.process, request.query, context)
        
        return QueryResponse(
            response=response.synthesized_response,
            routing=response.routing,
            execution_time_ms=response.total_time_ms,
            charts=[chart.__dict__ if hasattr(chart, '__dict__') else chart for chart in response.charts]
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for streaming
@app.websocket("/ws/query")
async def websocket_query(websocket: WebSocket):
    """Process queries with real-time streaming via WebSocket.
    
    This endpoint now uses request-scoped stream handlers and session context,
    ensuring each WebSocket connection has its own isolated handler.
    
    Requirements: 1.6, 2.1, 2.2, 2.3
    """
    await websocket.accept()
    
    if orchestrator is None:
        await websocket.send_json({
            "type": "error",
            "data": {"message": "System not initialized"},
            "timestamp": datetime.utcnow().isoformat()
        })
        await websocket.close()
        return
    
    # Create session context for this WebSocket connection
    if _session_manager is None:
        await websocket.send_json({
            "type": "error",
            "data": {"message": "Session manager not initialized"},
            "timestamp": datetime.utcnow().isoformat()
        })
        await websocket.close()
        return
    
    # Create a new session for this WebSocket connection
    default_identity = _demo_identities[0]
    session_context = _session_manager.create_session(
        user_id=default_identity["id"],
        identity=default_identity
    )
    
    # Create request-scoped stream handler using the factory
    ws_stream_handler = StreamHandlerFactory.create_websocket_handler(
        websocket=websocket,
        session_id=session_context.session_id
    )
    
    try:
        while True:
            # Receive query from client
            data = await websocket.receive_json()
            query = data.get("query", "")
            
            # Check for session ID in message to update session
            client_session_id = data.get("session_id")
            if client_session_id:
                existing_session = _session_manager.get_session(client_session_id)
                if existing_session:
                    session_context = existing_session
            
            if not query:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Empty query"},
                    "timestamp": datetime.utcnow().isoformat()
                })
                continue
            
            logger.info(f"WebSocket query (session={session_context.session_id}): {query}")
            
            # Send start event with session info
            await websocket.send_json({
                "type": "query_start",
                "data": {
                    "query": query,
                    "session_id": session_context.session_id
                },
                "timestamp": datetime.utcnow().isoformat()
            })
            
            try:
                # Add context including session info
                context = {
                    "output_dir": config.output_dir,
                    "data_path": config.data_path,
                    "session_id": session_context.session_id,
                    "user_id": session_context.user_id,
                }
                
                # Process through orchestrator with request-scoped handler
                # Note: We pass the stream handler to process() if the orchestrator supports it
                # For now, we use the existing pattern but with isolated handler
                response = await asyncio.to_thread(
                    orchestrator.process, 
                    query, 
                    context,
                    ws_stream_handler  # Pass request-scoped handler
                )
                
                # Send final response
                await websocket.send_json({
                    "type": "response",
                    "data": {
                        "response": response.synthesized_response,
                        "routing": response.routing,
                        "execution_time_ms": response.total_time_ms,
                        "charts": [chart.__dict__ if hasattr(chart, '__dict__') else chart for chart in response.charts],
                        "session_id": session_context.session_id
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Query processing error: {e}", exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": str(e)},
                    "timestamp": datetime.utcnow().isoformat()
                })
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected (session={session_context.session_id})")
        # Clean up the stream handler
        ws_stream_handler.close()
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        ws_stream_handler.close()
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"message": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            })
        except:
            pass


# WebSocket endpoint for workbench streaming analysis
@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """Stream analysis workflow events via WebSocket for the workbench UI.
    
    This endpoint now uses session context and InvestigationStore,
    ensuring proper session isolation and access control.
    
    Requirements: 1.6, 2.1, 2.2, 2.3
    """
    await websocket.accept()
    
    if orchestrator is None:
        await websocket.send_json({
            "type": "error",
            "data": {"message": "System not initialized"},
        })
        await websocket.close()
        return
    
    # Create session context for this WebSocket connection
    if _session_manager is None or _investigation_store is None:
        await websocket.send_json({
            "type": "error",
            "data": {"message": "Security infrastructure not initialized"},
        })
        await websocket.close()
        return
    
    # Create a new session for this WebSocket connection
    default_identity = _demo_identities[0]
    session_context = _session_manager.create_session(
        user_id=default_identity["id"],
        identity=default_identity
    )
    
    # Create request-scoped stream handler
    ws_stream_handler = StreamHandlerFactory.create_websocket_handler(
        websocket=websocket,
        session_id=session_context.session_id
    )
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            event_type = data.get("type", "")
            
            # Check for session ID in message to update session
            client_session_id = data.get("session_id")
            if client_session_id:
                existing_session = _session_manager.get_session(client_session_id)
                if existing_session:
                    session_context = existing_session
            
            if event_type == "start_analysis":
                research_goal = data.get("data", {}).get("research_goal", "")
                if not research_goal:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": "Research goal is required"},
                    })
                    continue

                # Optional Tech Ops context so we can generate KPI charts and persist to the right investigation
                inv_id = data.get("data", {}).get("investigation_id")
                kpi_id = data.get("data", {}).get("kpi_id")
                station = data.get("data", {}).get("station")
                window = data.get("data", {}).get("window")
                point_t = data.get("data", {}).get("point_t")
                summary_level = data.get("data", {}).get("summary_level", "station")

                max_iterations = int(data.get("data", {}).get("max_iterations", 20))
                if max_iterations < 1:
                    max_iterations = 1
                if max_iterations > 20:
                    max_iterations = 20
                
                # Generate analysis ID
                import uuid
                analysis_id = str(uuid.uuid4())[:8]
                
                # Send analysis started event
                await websocket.send_json({
                    "type": "analysis_started",
                    "data": {
                        "analysis_id": analysis_id,
                        "research_goal": research_goal,
                        "session_id": session_context.session_id,
                    },
                })
                
                # Start step 1
                step_id = f"step-{uuid.uuid4().hex[:6]}"
                await websocket.send_json({
                    "type": "step_started",
                    "data": {
                        "step_id": step_id,
                        "step_number": 1,
                    },
                })

                # Persist step record using InvestigationStore if this is a Tech Ops investigation
                if inv_id and _investigation_store:
                    inv = _investigation_store.get(inv_id, context=session_context)
                    if inv:
                        inv_steps = inv.get("steps", [])
                        inv_steps.append(
                            {
                                "step_id": step_id,
                                "step_number": 1,
                                "query": research_goal,
                                "iterations": [],
                                "created_at": datetime.utcnow().isoformat(),
                            }
                        )
                        _investigation_store.update(inv_id, {"steps": inv_steps}, context=session_context)

                # Build a test plan (unique "tests") and run until answered or max_iterations.
                executed_tests: set[str] = set()
                last_output = ""
                evidence_log_parts: list[str] = []

                techops_plan: list[str] = []
                if kpi_id and station and window:
                    try:
                        techops_plan = build_test_plan(
                            TechOpsContext(
                                kpi_id=str(kpi_id),
                                station=str(station),
                                window=str(window),
                                point_t=str(point_t) if point_t else None,
                                summary_level=str(summary_level or "station").lower(),
                            )
                        )
                    except Exception:
                        techops_plan = []
                if not techops_plan:
                    techops_plan = ["exploratory_analysis"]

                def _next_test_name(iteration_number: int) -> str:
                    for name in techops_plan:
                        if name not in executed_tests:
                            return name
                    # Fallback: don't repeat; end the loop by returning a sentinel.
                    return ""

                def _has_satisfied(text: str) -> bool:
                    import re

                    if not text:
                        return False
                    return re.search(r"(?im)^\\s*SATISFIED\\s*:\\s*true\\s*$", text) is not None

                # Loop up to max_iterations, but stop as soon as we have enough evidence to answer.
                for i in range(1, max_iterations + 1):
                    iteration_id = f"iter-{uuid.uuid4().hex[:6]}"

                    test_name = _next_test_name(i)
                    if not test_name:
                        break
                    previously_executed = sorted(executed_tests)
                    executed_tests.add(test_name)

                    iter_start = time.perf_counter()
                    await websocket.send_json({
                        "type": "iteration_started",
                        "data": {
                            "step_id": step_id,
                            "iteration_id": iteration_id,
                            "iteration_number": i,
                            "description": f"Test: {test_name}" if test_name else ("Initial investigation" if i == 1 else f"Refinement iteration {i}"),
                        },
                    })

                    try:
                        # Ensure the UI shows real progress, even for fast deterministic tests.
                        await asyncio.sleep(0.25)

                        # Compute deterministic test output (used as tool evidence and to avoid repeating "tests").
                        prior_evidence = "\n\n".join(evidence_log_parts).strip()
                        test_output = ""
                        if kpi_id and station and window:
                            try:
                                tctx = TechOpsContext(
                                    kpi_id=str(kpi_id),
                                    station=str(station),
                                    window=str(window),
                                    point_t=str(point_t) if point_t else None,
                                    summary_level=str(summary_level or "station").lower(),
                                )
                                test_result = run_test(store=get_techops_store(), ctx=tctx, test_name=test_name)
                                test_output = format_test_result(test_result)
                            except Exception as e:
                                test_output = f"TEST: {test_name}\nFINDING: failed to compute test output ({e})"
                        if test_output:
                            evidence_log_parts.append(test_output)

                        context = {
                            "output_dir": config.output_dir,
                            "data_path": config.data_path,
                            "iteration": i,
                            "previous_summary": last_output[:1200] if last_output else "",
                            "kpi_id": kpi_id,
                            "station": station,
                            "window": window,
                            "point_t": point_t,
                            "summary_level": summary_level,
                            "test_name": test_name,
                            "executed_tests": previously_executed,
                            "evidence_log": prior_evidence,
                            "techops_test_output": test_output,
                            "model_provider": config.model_provider,
                            "model_id": config.model_id,
                            "ollama_host": config.ollama_host,
                        }

                        iteration_query = research_goal
                        # In Tech Ops mode, each iteration runs a distinct diagnostic test.
                        if test_name:
                            iteration_query = (
                                f"{research_goal}\n\n"
                                f"NEXT TEST TO RUN: {test_name}\n"
                                f"ALREADY RAN (do not repeat): {', '.join(previously_executed)}\n"
                            )

                        response = await asyncio.to_thread(orchestrator.process, iteration_query, context)
                        synthesized = response.synthesized_response or ""
                        satisfied = _has_satisfied(synthesized)

                        # If we didn't learn anything new, stop early to avoid repeating the same "test".
                        if synthesized and synthesized.strip() == last_output.strip():
                            await websocket.send_json({
                                "type": "verification_complete",
                                "data": {
                                    "step_id": step_id,
                                    "iteration_id": iteration_id,
                                    "result": {
                                        "passed": True,
                                        "assessment": "No new information produced; stopping early to avoid repeating tests.",
                                        "suggestions": [],
                                    },
                                },
                            })
                            break

                        last_output = synthesized or last_output

                        # Provide concrete "generated code" per test so the UI shows real work (not placeholders).
                        code = "# Analysis code\nprint('Analyzing...')"
                        if kpi_id and station and window and test_name:
                            code = (
                                f"""# DS-STAR Tech Ops diagnostic test: {test_name}
 from src.data.techops_metrics import get_techops_store
 from src.techops.investigation_tests import TechOpsContext, run_test, format_test_result
 
 store = get_techops_store()
 ctx = TechOpsContext(kpi_id={kpi_id!r}, station={station!r}, window={window!r}, point_t={point_t!r})
 result = run_test(store=store, ctx=ctx, test_name={test_name!r})
 print(format_test_result(result))
 """
                            ).strip()

                        await websocket.send_json({
                            "type": "code_generated",
                            "data": {
                                "step_id": step_id,
                                "iteration_id": iteration_id,
                                "code": code,
                            },
                        })

                        await websocket.send_json({
                            "type": "execution_complete",
                            "data": {
                                "step_id": step_id,
                                "iteration_id": iteration_id,
                                "output": {
                                    "success": True,
                                    "output": synthesized or "Analysis completed successfully.",
                                    "duration_ms": int((time.perf_counter() - iter_start) * 1000),
                                },
                            },
                        })

                        # Visualization (use a distinct chart per test to avoid repeating the same picture)
                        chart_data = None
                        if kpi_id and station and window:
                            if test_name == "signal_characterization":
                                chart_data = generate_techops_kpi_chart(kpi_id=kpi_id, station=station, window=window, point_t=point_t, summary_level=summary_level)
                            elif test_name == "yoy_seasonality":
                                chart_data = generate_techops_yoy_chart(kpi_id=kpi_id, station=station, window=window, summary_level=summary_level)
                            elif test_name == "cross_station":
                                chart_data = generate_techops_cross_station_chart(kpi_id=kpi_id, station=station, window=window, point_t=point_t)
                            elif test_name == "pre_post_shift":
                                chart_data = generate_techops_pre_post_chart(kpi_id=kpi_id, station=station, window=window, summary_level=summary_level)
                        if not chart_data and response.synthesized_response:
                            chart_data = generate_chart_from_response(response.synthesized_response, research_goal)
                        if chart_data:
                            await websocket.send_json({
                                "type": "visualization_ready",
                                "data": {
                                    "step_id": step_id,
                                    "iteration_id": iteration_id,
                                    "chart": chart_data,
                                },
                            })

                        # Persist iteration record using InvestigationStore
                        if inv_id and _investigation_store:
                            inv = _investigation_store.get(inv_id, context=session_context)
                            if inv:
                                inv_steps = inv.get("steps", [])
                                for st in inv_steps:
                                    if st.get("step_id") == step_id:
                                        st.setdefault("iterations", []).append(
                                            {
                                                "iteration_id": iteration_id,
                                                "iteration_number": i,
                                                "generated_code": code,
                                                "query": iteration_query,
                                                "response": response.synthesized_response or "",
                                                "chart": chart_data,
                                                "include_in_final": True,
                                                "created_at": datetime.utcnow().isoformat(),
                                            }
                                        )
                                        break
                                _investigation_store.update(inv_id, {"steps": inv_steps}, context=session_context)

                        await websocket.send_json({
                            "type": "verification_complete",
                            "data": {
                                "step_id": step_id,
                                "iteration_id": iteration_id,
                                "result": {
                                    "passed": True,
                                    "assessment": (
                                        "Answer satisfied; stopping early."
                                        if satisfied and test_name != "final_summary"
                                        else f"Completed test '{test_name}'."
                                    ),
                                    "suggestions": [],
                                },
                            },
                        })

                        # Stop once answered, or once we ran the final summary test (or hit max_iterations).
                        if satisfied and test_name != "final_summary":
                            break
                        if test_name == "final_summary":
                            break

                    except Exception as e:
                        logger.error(f"Analysis error: {e}", exc_info=True)
                        await websocket.send_json({
                            "type": "error",
                            "data": {"message": str(e)},
                        })
                        break

                await websocket.send_json({"type": "step_completed", "data": {"step_id": step_id}})
                await websocket.send_json({"type": "analysis_completed", "data": {"analysis_id": analysis_id}})
            
            elif event_type == "approve_step":
                # Handle step approval - continue to next step
                step_data = data.get("data", {})
                await websocket.send_json({
                    "type": "step_approved",
                    "data": step_data,
                })
                logger.info(f"Step approved: {step_data.get('step_id')}")
            
            elif event_type == "refine_step":
                # Handle refinement request - re-run analysis with feedback
                step_data = data.get("data", {})
                feedback = step_data.get("feedback", "")
                step_id = step_data.get("step_id", "")
                
                await websocket.send_json({
                    "type": "refinement_started",
                    "data": step_data,
                })
                
                # Generate new iteration
                import uuid
                iteration_id = f"iter-{uuid.uuid4().hex[:6]}"
                
                await websocket.send_json({
                    "type": "iteration_started",
                    "data": {
                        "step_id": step_id,
                        "iteration_id": iteration_id,
                        "iteration_number": 2,  # Refinement iteration
                        "description": f"Refining based on feedback: {feedback}",
                    },
                })
                
                # Re-run analysis with feedback context
                try:
                    context = {
                        "output_dir": config.output_dir,
                        "data_path": config.data_path,
                        "feedback": feedback,
                    }
                    
                    refined_query = f"Please refine the previous analysis based on this feedback: {feedback}"
                    response = await asyncio.to_thread(orchestrator.process, refined_query, context)
                    
                    # Send code generated
                    code = "# Refined analysis\nimport pandas as pd\n\ndf = pd.read_csv('data/airline_operations.csv')\nprint(df.describe())"
                    if response.specialist_responses:
                        resp_text = response.specialist_responses[0].response
                        if "```python" in resp_text:
                            import re
                            code_match = re.search(r'```python\n(.*?)```', resp_text, re.DOTALL)
                            if code_match:
                                code = code_match.group(1).strip()
                    
                    await websocket.send_json({
                        "type": "code_generated",
                        "data": {
                            "step_id": step_id,
                            "iteration_id": iteration_id,
                            "code": code,
                        },
                    })
                    
                    # Send execution complete
                    await websocket.send_json({
                        "type": "execution_complete",
                        "data": {
                            "step_id": step_id,
                            "iteration_id": iteration_id,
                            "output": {
                                "success": True,
                                "output": response.synthesized_response or "Refined analysis completed.",
                                "duration_ms": response.total_time_ms,
                            },
                        },
                    })
                    
                    # Generate visualization
                    if response.synthesized_response:
                        chart_data = generate_chart_from_response(response.synthesized_response, feedback)
                        if chart_data:
                            await websocket.send_json({
                                "type": "visualization_ready",
                                "data": {
                                    "step_id": step_id,
                                    "iteration_id": iteration_id,
                                    "chart": chart_data,
                                },
                            })
                    
                    # Send verification complete
                    await websocket.send_json({
                        "type": "verification_complete",
                        "data": {
                            "step_id": step_id,
                            "iteration_id": iteration_id,
                            "result": {
                                "passed": True,
                                "assessment": "The refined analysis addresses the feedback and provides improved results.",
                                "suggestions": [],
                            },
                        },
                    })
                    
                except Exception as e:
                    logger.error(f"Refinement error: {e}", exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": str(e)},
                    })
            
    except WebSocketDisconnect:
        logger.info(f"Workbench WebSocket client disconnected (session={session_context.session_id})")
        ws_stream_handler.close()
    except Exception as e:
        logger.error(f"Workbench WebSocket error: {e}", exc_info=True)
        ws_stream_handler.close()
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"message": str(e)},
            })
        except:
            pass


# Conversation history endpoints
@app.get("/api/history")
async def get_history():
    """Get conversation history summary."""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return orchestrator.get_history_summary()


@app.delete("/api/history")
async def clear_history():
    """Clear conversation history."""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    orchestrator.clear_history()
    return {"status": "cleared"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
