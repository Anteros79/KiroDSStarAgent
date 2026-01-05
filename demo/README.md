# DS-STAR Demo Materials

This directory contains materials for demonstrating the DS-STAR multi-agent system.

**Last Updated:** January 4, 2026

## Contents

| File | Description |
|------|-------------|
| `sample_queries.md` | Example queries organized by specialist type |
| `demo_scenarios.md` | Pre-built demo scenarios with expected outputs |
| `run_demo.py` | Automated demo script |

## Quick Start

### Prerequisites

DS-STAR supports 5 model providers. Configure your preferred provider in `.env`:
- **Lemonade** (default) - Local execution on AMD Ryzen AI
- **Anthropic** - Claude models via API
- **OpenAI** - GPT-4 models via API
- **Ollama** - Local execution on any hardware
- **AWS Bedrock** - Enterprise AWS deployments

See `PROVIDER_QUICK_REFERENCE.md` for setup details.

### Interactive Demo (Recommended)

```bash
python demo/run_demo.py
```

Pauses between scenarios for presenter explanation.

### Automated Demo

```bash
python demo/run_demo.py --auto
```

### Verbose Mode

```bash
python demo/run_demo.py --verbose
```

Shows detailed investigation stream output.

## Demo Scenarios

### 1. Data Analysis: On-Time Performance
- **Routing**: Data Analyst only
- **Demonstrates**: Statistical analysis, KPI calculations
- **Query**: "What is the average delay by airline?"

### 2. Machine Learning: Delay Prediction
- **Routing**: ML Engineer (+ Data Analyst for context)
- **Demonstrates**: Model recommendations, code generation
- **Query**: "How can I predict flight delays?"

### 3. Visualization: Delay Distribution
- **Routing**: Data Analyst → Visualization Expert
- **Demonstrates**: Chart creation, Plotly JSON output
- **Query**: "Create a bar chart of delays by airline"

### 4. Multi-Domain: Comprehensive Analysis
- **Routing**: Data Analyst → ML Engineer → Visualization Expert
- **Demonstrates**: Star topology, response synthesis
- **Query**: "Analyze delays, recommend a prediction model, and visualize the results"

### 5. Tech Ops Investigation
- **Routing**: Orchestrator → Diagnostic Tests → LLM Interpretation
- **Demonstrates**: Wheeler XmR, signal detection, root cause analysis
- **Scenario**: PHX Parts Shortage

## Tech Ops Demo Scenarios

Pre-built scenarios in `src/data/demo_scenarios.py`:

### PHX Parts Shortage
- **Station**: Phoenix (PHX)
- **KPI**: OTP MX Rate
- **Root Cause**: Parts availability issue from supplier delay
- **Expected Findings**:
  - Signal characterization: Rule #1 violation
  - Cross-station: PHX isolated from peers
  - Pre/post shift: Sustained degradation

### DAL Weather Cascade
- **Station**: Dallas (DAL)
- **KPI**: EMO MX Rate
- **Root Cause**: Weather event triggering maintenance cascade
- **Expected Findings**:
  - Signal characterization: Stage change detected
  - YoY seasonality: Unusual for season
  - Cross-station: DAL-specific impact

### Fleet-Wide Fault Rate
- **Scope**: Company-wide
- **KPI**: Fault Rate
- **Root Cause**: EICAS software update affecting fault detection
- **Expected Findings**:
  - Cross-station: All stations affected equally
  - Pre/post shift: Clear before/after pattern

## Diagnostic Test Flow

```
Investigation Created
        │
        ▼
┌───────────────────┐
│ Signal            │ → Identifies Rule #1 violations
│ Characterization  │   Stage changes, MR signals
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ YoY Seasonality   │ → Compares to year-over-year
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Cross-Station     │ → Benchmarks against peers
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Pre/Post Shift    │ → Detects mean shifts
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Final Summary     │ → Synthesizes with confidence
└───────────────────┘
```

## Presenter Tips

### Before the Demo
- Test credentials and model connectivity
- Review `sample_queries.md` for routing behavior
- Prepare talking points for each scenario
- Consider running verbose mode to show investigation details

### During the Demo
- Use interactive mode to control pacing
- Explain the star topology when showing multi-domain queries
- Highlight the investigation stream output
- Point out response synthesis from multiple specialists
- Show the chart specification JSON output

### Key Points to Emphasize
- **Star Topology**: Central orchestrator coordinates all specialists
- **Intelligent Routing**: Automatic query analysis and specialist selection
- **Wheeler XmR**: Industry-standard SPC methodology
- **Confidence Scoring**: Each diagnostic test returns confidence levels
- **Transparency**: Investigation stream shows all reasoning steps

## Command-Line Options

```bash
python demo/run_demo.py [OPTIONS]

Options:
  --auto              Auto-advance through scenarios
  --verbose           Show detailed investigation output
  --model MODEL_ID    Override model ID
  --region REGION     Override AWS region
  --config FILE       Load from config file
```

## Troubleshooting

| Error | Solution |
|-------|----------|
| "strands-agents not installed" | `pip install strands-agents strands-agents-tools` |
| "Failed to validate credentials" | Check AWS credentials or API keys |
| "FileNotFoundError: airline_operations.csv" | Run `python src/data/generate_sample_data.py` |
| "ECONNREFUSED 127.0.0.1:8000" | Start backend with `start_backend.bat` |

## Customizing Scenarios

Add new scenarios in `run_demo.py`:

```python
DemoScenario(
    title="Your Scenario Title",
    query="Your query here",
    explanation="Presenter notes",
    expected_routing=["data_analyst", "visualization_expert"],
    pause_duration=5.0
)
```

## Related Documentation

- `CODE_REVIEW_SUMMARY.md` - Code quality and security findings
- `AGENTIC_FRAMEWORK_ANALYSIS.md` - Agent prompt analysis
- `docs/architecture.html` - System architecture
- `docs/agent-flow.html` - Agent flow diagrams
