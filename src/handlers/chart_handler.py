"""Chart output handler for DS-Star multi-agent system.

This module provides data structures and handlers for chart specifications
that can be used for both local rendering (matplotlib) and web rendering (Plotly).
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass
class AxisConfig:
    """Configuration for chart axis."""
    
    label: str
    scale: str = "linear"  # "linear", "log", "time"
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ChartSpecification:
    """Specification for a chart that can be rendered in multiple formats.
    
    Attributes:
        chart_type: Type of chart (bar, line, scatter, pie, histogram)
        title: Chart title
        data: List of data points/series as dictionaries
        x_axis: Configuration for x-axis (optional)
        y_axis: Configuration for y-axis (optional)
        styling: Additional styling options (colors, fonts, etc.)
        plotly_json: Plotly JSON specification for web rendering
        matplotlib_code: Python code for matplotlib rendering
    """
    
    chart_type: str
    title: str
    data: List[Dict]
    x_axis: Optional[AxisConfig] = None
    y_axis: Optional[AxisConfig] = None
    styling: Dict = None
    plotly_json: Dict = None
    matplotlib_code: str = ""
    
    def __post_init__(self):
        """Initialize default values."""
        if self.styling is None:
            self.styling = {}
        if self.plotly_json is None:
            self.plotly_json = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "chart_type": self.chart_type,
            "title": self.title,
            "data": self.data,
            "styling": self.styling,
            "plotly_json": self.plotly_json,
            "matplotlib_code": self.matplotlib_code
        }
        
        if self.x_axis:
            result["x_axis"] = self.x_axis.to_dict()
        if self.y_axis:
            result["y_axis"] = self.y_axis.to_dict()
            
        return result


class ChartOutputHandler:
    """Handles saving and generating chart specifications.
    
    This handler manages chart output in multiple formats:
    - JSON specification files for persistence
    - Plotly JSON for web rendering
    - Matplotlib code for local rendering
    """
    
    def __init__(self, output_dir: str):
        """Initialize the chart output handler.
        
        Args:
            output_dir: Directory path where chart specifications will be saved
        """
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self) -> None:
        """Create output directory if it doesn't exist."""
        os.makedirs(self.output_dir, exist_ok=True)
    
    def save_chart_spec(self, spec: ChartSpecification, filename: str) -> str:
        """Save chart specification to JSON file.
        
        Args:
            spec: ChartSpecification to save
            filename: Name of the output file (without path)
        
        Returns:
            Full path to the saved file
        """
        # Ensure filename has .json extension
        if not filename.endswith('.json'):
            filename = f"{filename}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Convert spec to dictionary and save as JSON
        spec_dict = spec.to_dict()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(spec_dict, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def generate_plotly_json(self, spec: ChartSpecification) -> Dict:
        """Generate Plotly JSON specification from chart spec.
        
        This method creates a web-ready Plotly JSON specification that can be
        used directly with Plotly.js for interactive web visualizations.
        
        Args:
            spec: ChartSpecification to convert
        
        Returns:
            Dictionary containing Plotly JSON specification
        """
        # Base plotly structure
        plotly_spec = {
            "data": [],
            "layout": {
                "title": spec.title,
                "showlegend": True
            }
        }
        
        # Add axis configurations if present
        if spec.x_axis:
            plotly_spec["layout"]["xaxis"] = {
                "title": spec.x_axis.label,
                "type": spec.x_axis.scale
            }
            if spec.x_axis.min_value is not None:
                plotly_spec["layout"]["xaxis"]["range"] = [
                    spec.x_axis.min_value,
                    spec.x_axis.max_value
                ]
        
        if spec.y_axis:
            plotly_spec["layout"]["yaxis"] = {
                "title": spec.y_axis.label,
                "type": spec.y_axis.scale
            }
            if spec.y_axis.min_value is not None:
                plotly_spec["layout"]["yaxis"]["range"] = [
                    spec.y_axis.min_value,
                    spec.y_axis.max_value
                ]
        
        # Convert chart type and data to Plotly format
        if spec.chart_type in ["bar", "line", "scatter"]:
            trace = {
                "type": spec.chart_type,
                "name": spec.title
            }
            
            # Extract x and y values from data
            if spec.data:
                # Assume data is list of dicts with 'x' and 'y' keys
                if all('x' in d and 'y' in d for d in spec.data):
                    trace["x"] = [d['x'] for d in spec.data]
                    trace["y"] = [d['y'] for d in spec.data]
                else:
                    # Fallback: use data as-is
                    trace["x"] = list(range(len(spec.data)))
                    trace["y"] = spec.data
            
            plotly_spec["data"].append(trace)
            
        elif spec.chart_type == "pie":
            trace = {
                "type": "pie",
                "labels": [d.get('label', f"Item {i}") for i, d in enumerate(spec.data)],
                "values": [d.get('value', 0) for d in spec.data]
            }
            plotly_spec["data"].append(trace)
            
        elif spec.chart_type == "histogram":
            trace = {
                "type": "histogram",
                "x": [d.get('value', d.get('x', 0)) for d in spec.data]
            }
            plotly_spec["data"].append(trace)
        
        # Apply custom styling (default to Southwest Tech Ops palette where applicable)
        if spec.styling:
            if "colors" in spec.styling:
                plotly_spec["layout"]["colorway"] = spec.styling["colors"]
            if "template" in spec.styling:
                plotly_spec["layout"]["template"] = spec.styling["template"]
        else:
            plotly_spec["layout"]["colorway"] = ["#304CB2", "#C4122F", "#FFB612", "#111827", "#6B7280"]
        
        return plotly_spec
