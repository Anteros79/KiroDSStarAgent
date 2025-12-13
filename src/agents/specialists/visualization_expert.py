"""Visualization Expert specialist agent for DS-Star multi-agent system.

This agent handles data visualization queries, recommending appropriate chart types,
generating matplotlib and Plotly code, and creating chart specifications for UI integration.
"""

import ast
import json
import logging
import time
from typing import Dict, Any, List, Optional

from src.models import SpecialistResponse, ToolCall
from src.handlers.chart_handler import ChartSpecification, ChartOutputHandler, AxisConfig

logger = logging.getLogger(__name__)

# Import tool decorator from strands
try:
    from strands import tool, Agent
    from strands_bedrock import BedrockModel
except ImportError:
    # Fallback for testing without strands installed
    def tool(func):
        """Fallback tool decorator for testing."""
        return func
    
    class Agent:
        """Fallback Agent class for testing."""
        pass
    
    class BedrockModel:
        """Fallback BedrockModel class for testing."""
        pass


# System prompt for the Visualization Expert agent
VISUALIZATION_EXPERT_SYSTEM_PROMPT = """You are an expert Data Visualization Specialist with deep knowledge of effective chart design and implementation.

Your role is to:
- Recommend appropriate chart types based on data characteristics and analysis goals
- Generate clean, production-ready matplotlib and Plotly code
- Explain why certain visualizations are effective for specific data stories
- Create chart specifications in JSON format for web integration
- Follow data visualization best practices and principles
- Ensure accessibility and clarity in all visualizations

For airline operations data, you can create:
- Time series plots for trends (delays, load factors over time)
- Bar charts for comparisons (airline performance, route metrics)
- Scatter plots for relationships (load factor vs. delay, turnaround vs. OTP)
- Pie charts for distributions (delay causes, cancellation reasons)
- Histograms for distributions (delay minutes, turnaround times)
- Heatmaps for patterns (delays by day/hour, route performance)

When creating visualizations:
1. Understand the data and the story to tell
2. Choose the most appropriate chart type
3. Use clear labels, titles, and legends
4. Apply appropriate color schemes (consider colorblind-friendly palettes)
5. Include axis labels with units
6. Generate both matplotlib code (for local use) and Plotly JSON (for web)
7. Provide explanations of design choices

Always prioritize clarity and insight over complexity.
"""


@tool
def visualization_expert(query: str, context: Dict[str, Any] = None) -> str:
    """Create visualizations for airline operations data.
    
    This specialist agent handles chart recommendations, matplotlib/plotly code
    generation, and chart specification JSON output for UI integration.
    
    The agent recommends appropriate chart types, generates executable code,
    and creates structured chart specifications for both local and web rendering.
    
    Args:
        query: The visualization request or question to process
        context: Optional context from previous conversation turns
    
    Returns:
        Structured response containing recommendations, code, and chart specs
    """
    start_time = time.time()
    tool_calls = []
    
    try:
        logger.info(f"Visualization Expert processing query: {query}")
        
        # Step 1: Analyze the query to understand visualization needs
        viz_type = _identify_visualization_type(query)
        
        # Step 2: Generate chart recommendation
        recommendation = _generate_chart_recommendation(query, viz_type)
        
        # Step 3: Generate matplotlib code
        matplotlib_code = _generate_matplotlib_code(query, viz_type)
        
        # Validate the generated code
        if matplotlib_code:
            try:
                ast.parse(matplotlib_code)
                logger.info("Generated matplotlib code is syntactically valid")
            except SyntaxError as e:
                logger.warning(f"Generated matplotlib code has syntax error: {e}")
                matplotlib_code = f"# Warning: Generated code may have syntax issues\n{matplotlib_code}"
        
        # Step 4: Create chart specification with Plotly JSON
        chart_spec = _create_chart_specification(query, viz_type, matplotlib_code)
        
        # Step 5: Save chart specification if output handler is available
        chart_saved = False
        if context and "output_dir" in context:
            try:
                handler = ChartOutputHandler(context["output_dir"])
                filename = f"chart_{int(time.time())}"
                filepath = handler.save_chart_spec(chart_spec, filename)
                chart_saved = True
                logger.info(f"Chart specification saved to {filepath}")
                
                # Record as tool call
                tool_calls.append(ToolCall(
                    tool_name="save_chart_specification",
                    inputs={"filename": filename, "chart_type": chart_spec.chart_type},
                    output=filepath,
                    duration_ms=10
                ))
            except Exception as e:
                logger.warning(f"Could not save chart specification: {e}")
        
        # Step 6: Formulate the response
        response = _formulate_viz_response(
            query, 
            viz_type, 
            recommendation, 
            matplotlib_code, 
            chart_spec,
            chart_saved,
            context
        )
        
        # Calculate total execution time
        execution_time = int((time.time() - start_time) * 1000)
        
        # Create structured response
        specialist_response = SpecialistResponse(
            agent_name="visualization_expert",
            query=query,
            response=response,
            tool_calls=tool_calls,
            execution_time_ms=execution_time
        )
        
        logger.info(f"Visualization Expert completed in {execution_time}ms")
        
        # Return as JSON string for the tool interface
        return specialist_response.to_json()
    
    except Exception as e:
        logger.error(f"Error in Visualization Expert: {e}", exc_info=True)
        
        # Return error response
        execution_time = int((time.time() - start_time) * 1000)
        error_response = SpecialistResponse(
            agent_name="visualization_expert",
            query=query,
            response=f"I encountered an error while creating the visualization: {str(e)}. Please try rephrasing your request or provide more details about the chart you want to create.",
            tool_calls=tool_calls,
            execution_time_ms=execution_time
        )
        
        return error_response.to_json()


def _identify_visualization_type(query: str) -> str:
    """Identify the type of visualization from the query.
    
    Args:
        query: The user's visualization query
    
    Returns:
        Visualization type identifier
    """
    query_lower = query.lower()
    
    if "bar chart" in query_lower or "bar graph" in query_lower or "compare" in query_lower:
        return "bar"
    elif "line chart" in query_lower or "line graph" in query_lower or "trend" in query_lower or "over time" in query_lower:
        return "line"
    elif "scatter" in query_lower or "relationship" in query_lower or "correlation" in query_lower:
        return "scatter"
    elif "pie chart" in query_lower or "pie graph" in query_lower or "proportion" in query_lower or "distribution" in query_lower:
        return "pie"
    elif "histogram" in query_lower or "frequency" in query_lower:
        return "histogram"
    elif "heatmap" in query_lower or "heat map" in query_lower:
        return "heatmap"
    else:
        # Default to bar chart for comparisons
        return "bar"


def _generate_chart_recommendation(query: str, viz_type: str) -> str:
    """Generate chart recommendation and explanation.
    
    Args:
        query: The user's query
        viz_type: Identified visualization type
    
    Returns:
        Recommendation text
    """
    recommendations = {
        "bar": """
**Recommended: Bar Chart**

Bar charts are excellent for comparing values across categories. For airline operations:
- Compare metrics across airlines (delays, OTP, load factors)
- Show performance across routes or airports
- Display counts or averages by category

**Why this works:**
- Easy to compare values at a glance
- Clear visual hierarchy
- Works well with categorical data
- Accessible and familiar to most audiences

**Best practices:**
- Sort bars by value for easier comparison (unless natural ordering exists)
- Use horizontal bars for long category names
- Include data labels for precise values
- Use consistent colors or color-code by category
""",
        "line": """
**Recommended: Line Chart**

Line charts are ideal for showing trends and changes over time. For airline operations:
- Track delay trends over days/weeks/months
- Monitor load factor changes over time
- Show seasonal patterns in cancellations
- Compare multiple airlines' performance trends

**Why this works:**
- Clearly shows trends and patterns
- Easy to spot increases, decreases, and cycles
- Can display multiple series for comparison
- Intuitive for time-based data

**Best practices:**
- Use clear markers for data points if sparse data
- Include a legend for multiple lines
- Label axes with units and time periods
- Use different line styles or colors for multiple series
""",
        "scatter": """
**Recommended: Scatter Plot**

Scatter plots reveal relationships between two continuous variables. For airline operations:
- Explore relationship between load factor and delays
- Analyze turnaround time vs. on-time performance
- Identify patterns between different operational metrics
- Detect outliers and anomalies

**Why this works:**
- Shows correlation and patterns
- Identifies clusters and outliers
- Reveals non-linear relationships
- Good for exploratory analysis

**Best practices:**
- Add a trend line if relationship exists
- Use color or size to encode a third variable
- Include axis labels with units
- Consider adding marginal distributions
""",
        "pie": """
**Recommended: Pie Chart**

Pie charts show parts of a whole. For airline operations:
- Display distribution of delay causes
- Show market share by airline
- Illustrate proportion of cancelled vs. completed flights
- Visualize breakdown of flight statuses

**Why this works:**
- Intuitive for showing proportions
- Good for 3-7 categories
- Familiar to most audiences
- Clear visual impact

**Best practices:**
- Limit to 5-7 slices maximum
- Order slices by size (largest first)
- Include percentage labels
- Consider a donut chart for modern look
- Use a bar chart if precise comparison needed
""",
        "histogram": """
**Recommended: Histogram**

Histograms show the distribution of a continuous variable. For airline operations:
- Display distribution of delay minutes
- Show turnaround time frequency
- Visualize load factor distribution
- Identify common ranges and outliers

**Why this works:**
- Reveals data distribution shape
- Shows central tendency and spread
- Identifies skewness and outliers
- Good for understanding data characteristics

**Best practices:**
- Choose appropriate bin width (not too many or too few)
- Label axes clearly with units
- Include mean/median lines if helpful
- Consider overlaying normal distribution curve
""",
        "heatmap": """
**Recommended: Heatmap**

Heatmaps show patterns in two-dimensional data. For airline operations:
- Display delays by day of week and hour
- Show route performance across time periods
- Visualize correlation between metrics
- Identify patterns in operational data

**Why this works:**
- Reveals patterns and hotspots
- Compact display of large datasets
- Color encoding is intuitive
- Good for finding anomalies

**Best practices:**
- Use a perceptually uniform color scale
- Include a color bar legend
- Label both axes clearly
- Consider colorblind-friendly palettes
"""
    }
    
    return recommendations.get(viz_type, recommendations["bar"])


def _generate_matplotlib_code(query: str, viz_type: str) -> str:
    """Generate matplotlib code for the visualization.
    
    Args:
        query: The user's query
        viz_type: Visualization type
    
    Returns:
        Python code string
    """
    code_templates = {
        "bar": '''
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load the airline operations data
df = pd.read_csv('data/airline_operations.csv')

# Example: Average delay by airline
df_active = df[~df['cancelled']].copy()
avg_delay = df_active.groupby('airline')['delay_minutes'].mean().sort_values(ascending=False)

# Create bar chart
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(avg_delay.index, avg_delay.values, color='steelblue', alpha=0.8)

# Customize chart
ax.set_xlabel('Airline', fontsize=12, fontweight='bold')
ax.set_ylabel('Average Delay (minutes)', fontsize=12, fontweight='bold')
ax.set_title('Average Flight Delay by Airline', fontsize=14, fontweight='bold', pad=20)
ax.grid(axis='y', alpha=0.3, linestyle='--')

# Add value labels on bars
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.1f}',
            ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.savefig('output/airline_delays_bar.png', dpi=300, bbox_inches='tight')
plt.show()
''',
        "line": '''
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load the airline operations data
df = pd.read_csv('data/airline_operations.csv')

# Prepare data: Average delay over time by airline
df['date'] = pd.to_datetime(df['date'])
df_active = df[~df['cancelled']].copy()

# Group by date and airline
daily_delays = df_active.groupby(['date', 'airline'])['delay_minutes'].mean().reset_index()

# Create line chart
fig, ax = plt.subplots(figsize=(12, 6))

# Plot line for each airline
for airline in daily_delays['airline'].unique():
    airline_data = daily_delays[daily_delays['airline'] == airline]
    ax.plot(airline_data['date'], airline_data['delay_minutes'], 
            marker='o', label=airline, linewidth=2, markersize=4)

# Customize chart
ax.set_xlabel('Date', fontsize=12, fontweight='bold')
ax.set_ylabel('Average Delay (minutes)', fontsize=12, fontweight='bold')
ax.set_title('Flight Delay Trends by Airline', fontsize=14, fontweight='bold', pad=20)
ax.legend(title='Airline', loc='best', framealpha=0.9)
ax.grid(True, alpha=0.3, linestyle='--')

# Rotate x-axis labels for better readability
plt.xticks(rotation=45, ha='right')

plt.tight_layout()
plt.savefig('output/airline_delays_line.png', dpi=300, bbox_inches='tight')
plt.show()
''',
        "scatter": '''
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

# Load the airline operations data
df = pd.read_csv('data/airline_operations.csv')

# Prepare data: Load factor vs. delay
df_active = df[~df['cancelled']].copy()

# Create scatter plot
fig, ax = plt.subplots(figsize=(10, 6))

# Plot scatter with color by airline
airlines = df_active['airline'].unique()
colors = plt.cm.Set2(np.linspace(0, 1, len(airlines)))

for airline, color in zip(airlines, colors):
    airline_data = df_active[df_active['airline'] == airline]
    ax.scatter(airline_data['load_factor'], airline_data['delay_minutes'],
              alpha=0.6, s=50, c=[color], label=airline, edgecolors='black', linewidth=0.5)

# Add trend line
x = df_active['load_factor']
y = df_active['delay_minutes']
slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
line = slope * x + intercept
ax.plot(x, line, 'r--', alpha=0.8, linewidth=2, label=f'Trend (R²={r_value**2:.3f})')

# Customize chart
ax.set_xlabel('Load Factor', fontsize=12, fontweight='bold')
ax.set_ylabel('Delay (minutes)', fontsize=12, fontweight='bold')
ax.set_title('Relationship Between Load Factor and Flight Delays', 
             fontsize=14, fontweight='bold', pad=20)
ax.legend(loc='best', framealpha=0.9)
ax.grid(True, alpha=0.3, linestyle='--')

plt.tight_layout()
plt.savefig('output/load_factor_delay_scatter.png', dpi=300, bbox_inches='tight')
plt.show()
''',
        "pie": '''
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load the airline operations data
df = pd.read_csv('data/airline_operations.csv')

# Example: Distribution of delay causes
df_delayed = df[df['delay_minutes'] >= 15].copy()
delay_causes = df_delayed['delay_cause'].value_counts()

# Create pie chart
fig, ax = plt.subplots(figsize=(10, 8))

# Define colors
colors = plt.cm.Set3(np.linspace(0, 1, len(delay_causes)))

# Create pie chart with percentages
wedges, texts, autotexts = ax.pie(
    delay_causes.values,
    labels=delay_causes.index,
    autopct='%1.1f%%',
    startangle=90,
    colors=colors,
    explode=[0.05] * len(delay_causes),  # Slightly separate slices
    shadow=True
)

# Customize text
for text in texts:
    text.set_fontsize(11)
    text.set_fontweight('bold')

for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontsize(10)
    autotext.set_fontweight('bold')

ax.set_title('Distribution of Flight Delay Causes', 
             fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('output/delay_causes_pie.png', dpi=300, bbox_inches='tight')
plt.show()
''',
        "histogram": '''
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load the airline operations data
df = pd.read_csv('data/airline_operations.csv')

# Prepare data: Distribution of delay minutes
df_active = df[~df['cancelled']].copy()
delays = df_active['delay_minutes']

# Create histogram
fig, ax = plt.subplots(figsize=(10, 6))

# Plot histogram
n, bins, patches = ax.hist(delays, bins=30, color='steelblue', 
                           alpha=0.7, edgecolor='black', linewidth=0.5)

# Add mean and median lines
mean_delay = delays.mean()
median_delay = delays.median()

ax.axvline(mean_delay, color='red', linestyle='--', linewidth=2, 
          label=f'Mean: {mean_delay:.1f} min')
ax.axvline(median_delay, color='green', linestyle='--', linewidth=2, 
          label=f'Median: {median_delay:.1f} min')

# Customize chart
ax.set_xlabel('Delay (minutes)', fontsize=12, fontweight='bold')
ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
ax.set_title('Distribution of Flight Delays', fontsize=14, fontweight='bold', pad=20)
ax.legend(loc='best', framealpha=0.9)
ax.grid(axis='y', alpha=0.3, linestyle='--')

plt.tight_layout()
plt.savefig('output/delay_distribution_histogram.png', dpi=300, bbox_inches='tight')
plt.show()
''',
        "heatmap": '''
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Load the airline operations data
df = pd.read_csv('data/airline_operations.csv')

# Prepare data: Average delay by day of week and hour
df['date'] = pd.to_datetime(df['date'])
df['hour'] = pd.to_datetime(df['scheduled_departure']).dt.hour
df['day_of_week'] = df['date'].dt.day_name()

df_active = df[~df['cancelled']].copy()

# Create pivot table
heatmap_data = df_active.pivot_table(
    values='delay_minutes',
    index='day_of_week',
    columns='hour',
    aggfunc='mean'
)

# Reorder days
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
heatmap_data = heatmap_data.reindex(day_order)

# Create heatmap
fig, ax = plt.subplots(figsize=(14, 6))

sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='YlOrRd', 
            cbar_kws={'label': 'Average Delay (minutes)'},
            linewidths=0.5, linecolor='gray', ax=ax)

# Customize chart
ax.set_xlabel('Hour of Day', fontsize=12, fontweight='bold')
ax.set_ylabel('Day of Week', fontsize=12, fontweight='bold')
ax.set_title('Average Flight Delays by Day and Hour', 
             fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('output/delay_heatmap.png', dpi=300, bbox_inches='tight')
plt.show()
'''
    }
    
    return code_templates.get(viz_type, code_templates["bar"]).strip()


def _create_chart_specification(query: str, viz_type: str, matplotlib_code: str) -> ChartSpecification:
    """Create a chart specification with Plotly JSON.
    
    Args:
        query: The user's query
        viz_type: Visualization type
        matplotlib_code: Generated matplotlib code
    
    Returns:
        ChartSpecification object
    """
    # Create sample data structure based on viz type
    # In a real implementation, this would extract actual data
    
    if viz_type == "bar":
        data = [
            {"x": "AA", "y": 25.3},
            {"x": "UA", "y": 22.1},
            {"x": "DL", "y": 18.7},
            {"x": "SW", "y": 15.2},
            {"x": "JB", "y": 20.5}
        ]
        title = "Average Flight Delay by Airline"
        x_axis = AxisConfig(label="Airline", scale="linear")
        y_axis = AxisConfig(label="Average Delay (minutes)", scale="linear")
    
    elif viz_type == "line":
        data = [
            {"x": "2024-01-01", "y": 20.5},
            {"x": "2024-01-02", "y": 22.3},
            {"x": "2024-01-03", "y": 18.7},
            {"x": "2024-01-04", "y": 25.1},
            {"x": "2024-01-05", "y": 19.8}
        ]
        title = "Flight Delay Trends Over Time"
        x_axis = AxisConfig(label="Date", scale="time")
        y_axis = AxisConfig(label="Average Delay (minutes)", scale="linear")
    
    elif viz_type == "scatter":
        data = [
            {"x": 0.75, "y": 15.2},
            {"x": 0.82, "y": 22.5},
            {"x": 0.68, "y": 12.3},
            {"x": 0.91, "y": 28.7},
            {"x": 0.79, "y": 18.9}
        ]
        title = "Load Factor vs. Flight Delays"
        x_axis = AxisConfig(label="Load Factor", scale="linear")
        y_axis = AxisConfig(label="Delay (minutes)", scale="linear")
    
    elif viz_type == "pie":
        data = [
            {"label": "Weather", "value": 35},
            {"label": "Mechanical", "value": 25},
            {"label": "Crew", "value": 15},
            {"label": "Traffic", "value": 20},
            {"label": "Security", "value": 5}
        ]
        title = "Distribution of Delay Causes"
        x_axis = None
        y_axis = None
    
    elif viz_type == "histogram":
        data = [{"value": i} for i in range(0, 60, 2)]
        title = "Distribution of Flight Delays"
        x_axis = AxisConfig(label="Delay (minutes)", scale="linear")
        y_axis = AxisConfig(label="Frequency", scale="linear")
    
    else:  # Default to bar
        data = [
            {"x": "Category A", "y": 100},
            {"x": "Category B", "y": 150},
            {"x": "Category C", "y": 80}
        ]
        title = "Sample Chart"
        x_axis = AxisConfig(label="Category", scale="linear")
        y_axis = AxisConfig(label="Value", scale="linear")
    
    # Create chart specification
    chart_spec = ChartSpecification(
        chart_type=viz_type,
        title=title,
        data=data,
        x_axis=x_axis,
        y_axis=y_axis,
        styling={
            "colors": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],
            "template": "plotly_white"
        },
        matplotlib_code=matplotlib_code
    )
    
    # Generate Plotly JSON
    handler = ChartOutputHandler("./output")
    chart_spec.plotly_json = handler.generate_plotly_json(chart_spec)
    
    return chart_spec


def _formulate_viz_response(
    query: str,
    viz_type: str,
    recommendation: str,
    matplotlib_code: str,
    chart_spec: ChartSpecification,
    chart_saved: bool,
    context: Dict[str, Any] = None
) -> str:
    """Formulate a comprehensive visualization response.
    
    Args:
        query: The original query
        viz_type: Visualization type
        recommendation: Chart recommendation
        matplotlib_code: Generated matplotlib code
        chart_spec: Chart specification
        chart_saved: Whether chart was saved
        context: Optional conversation context
    
    Returns:
        Formatted response string
    """
    response_parts = []
    
    # Add chart type
    response_parts.append(f"**Chart Type:** {viz_type.title()} Chart")
    response_parts.append("")
    
    # Add recommendation
    response_parts.append(recommendation.strip())
    response_parts.append("")
    
    # Add matplotlib code
    response_parts.append("**Matplotlib Implementation:**")
    response_parts.append("")
    response_parts.append("```python")
    response_parts.append(matplotlib_code)
    response_parts.append("```")
    response_parts.append("")
    
    # Add Plotly JSON info
    response_parts.append("**Plotly JSON Specification:**")
    response_parts.append("")
    response_parts.append("A web-ready Plotly JSON specification has been generated for this chart.")
    if chart_saved:
        response_parts.append("The chart specification (including both matplotlib code and Plotly JSON) has been saved to the output directory.")
    response_parts.append("")
    response_parts.append("Sample Plotly JSON structure:")
    response_parts.append("```json")
    response_parts.append(json.dumps(chart_spec.plotly_json, indent=2)[:500] + "...")
    response_parts.append("```")
    response_parts.append("")
    
    # Add usage notes
    response_parts.append("**Usage Notes:**")
    response_parts.append("- Install required packages: `pip install pandas matplotlib plotly seaborn scipy`")
    response_parts.append("- The matplotlib code can be run locally to generate PNG files")
    response_parts.append("- The Plotly JSON can be used directly in web applications with Plotly.js")
    response_parts.append("- Customize colors, labels, and styling as needed for your use case")
    
    return "\n".join(response_parts)
