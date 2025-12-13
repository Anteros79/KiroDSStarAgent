# DS-Star Multi-Agent Demo: Sample Queries

This document contains example queries for demonstrating the DS-Star multi-agent system with airline operations data. Each query shows the expected routing behavior and specialist involvement.

## Data Analyst Queries

These queries focus on data exploration, statistical analysis, and KPI calculations.

### Query 1: Basic Data Exploration
**Query:** "What airlines are in the dataset and how many flights does each have?"

**Expected Routing:** Data Analyst Agent

**Reasoning:** This is a straightforward data exploration query requiring pandas operations to group and count records. The Data Analyst has access to the `query_airline_data` tool for this purpose.

**Expected Output:** Summary statistics showing flight counts per airline (AA, UA, DL, SW, JB).

---

### Query 2: On-Time Performance Analysis
**Query:** "Calculate the on-time performance rate for each airline. Which airline has the best OTP?"

**Expected Routing:** Data Analyst Agent

**Reasoning:** OTP calculation requires statistical analysis of delay data. The Data Analyst will filter flights with delay_minutes <= 15 (industry standard) and calculate percentages.

**Expected Output:** OTP percentages for each airline with ranking and insights.

---

### Query 3: Delay Cause Analysis
**Query:** "What are the most common delay causes across all flights? Break it down by percentage."

**Expected Routing:** Data Analyst Agent

**Reasoning:** This requires grouping by delay_cause and calculating distributions. Pure data analysis task.

**Expected Output:** Breakdown showing weather, mechanical, crew, traffic, and security delays with percentages.

---

### Query 4: Load Factor Trends
**Query:** "What's the average load factor by airline? Are there any routes with consistently low load factors?"

**Expected Routing:** Data Analyst Agent

**Reasoning:** Requires aggregation of load_factor data by airline and route. Statistical analysis of operational efficiency.

**Expected Output:** Average load factors per airline and identification of underperforming routes.

---

## ML Engineer Queries

These queries focus on machine learning recommendations, model selection, and predictive analytics.

### Query 5: Delay Prediction Model
**Query:** "I want to predict flight delays. What machine learning model should I use and how would I implement it?"

**Expected Routing:** ML Engineer Agent

**Reasoning:** This is a classic ML problem requiring model recommendation. The ML Engineer will suggest appropriate algorithms (Random Forest, XGBoost) and provide implementation guidance.

**Expected Output:** Model recommendations with trade-offs, feature engineering suggestions, and sample scikit-learn code.

---

### Query 6: Cancellation Risk Classification
**Query:** "Can you help me build a classifier to predict which flights are at risk of cancellation?"

**Expected Routing:** ML Engineer Agent

**Reasoning:** Binary classification problem. The ML Engineer will recommend classification algorithms and explain the approach.

**Expected Output:** Algorithm recommendations (Logistic Regression, Random Forest), feature selection advice, and code template.

---

### Query 7: Turnaround Time Optimization
**Query:** "What features are most important for predicting turnaround time? How would I build a regression model?"

**Expected Routing:** ML Engineer Agent

**Reasoning:** Regression problem with feature importance analysis. Requires ML expertise for model selection and feature engineering.

**Expected Output:** Regression model recommendations, feature importance techniques, and implementation code.

---

## Visualization Expert Queries

These queries focus on data visualization, chart recommendations, and visual analytics.

### Query 8: Delay Distribution Visualization
**Query:** "Create a visualization showing the distribution of delay times across all flights."

**Expected Routing:** Visualization Expert Agent

**Reasoning:** Visualization request requiring chart type selection and code generation. The Visualization Expert will recommend a histogram or box plot.

**Expected Output:** Matplotlib/Plotly code for histogram with appropriate binning, plus chart specification JSON.

---

### Query 9: Airline Performance Comparison
**Query:** "I need a chart comparing on-time performance across airlines. What's the best way to visualize this?"

**Expected Routing:** Visualization Expert Agent

**Reasoning:** Comparative visualization requiring chart recommendation. The expert will suggest bar charts or grouped visualizations.

**Expected Output:** Bar chart code with OTP percentages, styling recommendations, and chart specification JSON.

---

### Query 10: Time Series Trend
**Query:** "Show me how delays have trended over time. I want to see if there are any patterns."

**Expected Routing:** Visualization Expert Agent

**Reasoning:** Time series visualization requiring line charts or area plots. The expert will handle temporal data visualization.

**Expected Output:** Line chart code with date on x-axis and delay metrics on y-axis, plus chart specification JSON.

---

## Multi-Domain Queries

These queries span multiple specialist domains and require coordination by the Orchestrator.

### Query 11: Comprehensive Delay Analysis
**Query:** "Analyze the delay patterns in the data, recommend a model to predict delays, and create visualizations showing the key insights."

**Expected Routing:** Data Analyst → ML Engineer → Visualization Expert

**Reasoning:** This query requires:
1. Data Analyst: Statistical analysis of delay patterns and distributions
2. ML Engineer: Model recommendations for delay prediction
3. Visualization Expert: Charts to visualize the findings

**Expected Output:** Comprehensive response synthesizing insights from all three specialists with analysis, model recommendations, and visualizations.

---

### Query 12: Load Factor Optimization Strategy
**Query:** "What routes have low load factors, what factors might predict load factor, and how can I visualize this to present to management?"

**Expected Routing:** Data Analyst → ML Engineer → Visualization Expert

**Reasoning:** This query requires:
1. Data Analyst: Identify low load factor routes and calculate statistics
2. ML Engineer: Suggest predictive models for load factor optimization
3. Visualization Expert: Create executive-friendly visualizations

**Expected Output:** Multi-faceted response with data insights, ML strategy, and presentation-ready charts.

---

### Query 13: Operational Efficiency Dashboard
**Query:** "I need to understand our operational efficiency. Analyze turnaround times, suggest ways to predict bottlenecks, and create a dashboard visualization."

**Expected Routing:** Data Analyst → ML Engineer → Visualization Expert

**Reasoning:** This query requires:
1. Data Analyst: Turnaround time analysis and bottleneck identification
2. ML Engineer: Predictive modeling for operational bottlenecks
3. Visualization Expert: Dashboard-style visualizations with multiple metrics

**Expected Output:** Complete operational efficiency analysis with predictive insights and dashboard specifications.

---

## Edge Cases and Ambiguous Queries

### Query 14: Ambiguous Intent
**Query:** "Tell me about the flights."

**Expected Routing:** Data Analyst Agent (default for data questions)

**Reasoning:** Ambiguous query defaults to data exploration. The Orchestrator will route to Data Analyst for general dataset overview.

**Expected Output:** High-level dataset summary with key statistics.

---

### Query 15: Conversational Follow-up
**Query:** (After Query 2) "Now show me a chart of those results."

**Expected Routing:** Visualization Expert Agent

**Reasoning:** Follow-up query leveraging conversation context. The Orchestrator passes previous OTP analysis results to the Visualization Expert.

**Expected Output:** Bar chart visualizing the OTP data from the previous query.

---

## Demo Presentation Tips

### For Data Analyst Queries:
- Highlight the investigation stream showing pandas operations
- Point out how the agent breaks down complex queries into steps
- Show the structured response format

### For ML Engineer Queries:
- Emphasize the model recommendation reasoning
- Show the generated code and explain its components
- Discuss trade-offs mentioned by the agent

### For Visualization Expert Queries:
- Display the dual output format (matplotlib + Plotly JSON)
- Show the chart specification structure for UI integration
- Demonstrate the styling and customization options

### For Multi-Domain Queries:
- Emphasize the star topology in action
- Show the routing decisions in the investigation stream
- Highlight how context flows between specialists
- Demonstrate response synthesis by the Orchestrator

### Investigation Stream Highlights:
- Agent start/end events showing specialist invocations
- Tool calls with inputs and outputs
- Routing decisions with reasoning
- Intermediate results before final synthesis
