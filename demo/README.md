# DS-Star Demo Materials

This directory contains materials for demonstrating the DS-Star multi-agent system.

## Files

### `sample_queries.md`
A comprehensive collection of example queries organized by specialist type:
- **Data Analyst queries**: Statistical analysis, KPI calculations, data exploration
- **ML Engineer queries**: Model recommendations, predictive analytics
- **Visualization Expert queries**: Chart creation, visualization guidance
- **Multi-domain queries**: Complex queries requiring multiple specialists
- **Edge cases**: Ambiguous queries and conversational follow-ups

Each query includes:
- The query text
- Expected routing behavior
- Reasoning explanation
- Expected output description

Use this file as a reference when preparing demos or testing the system.

### `run_demo.py`
An automated demo script that showcases the DS-Star system's capabilities through a series of pre-configured scenarios.

#### Features:
- **6 demo scenarios** covering single-domain and multi-domain queries
- **Interactive mode** with pauses for presenter explanation
- **Auto-advance mode** for unattended demonstrations
- **Verbose mode** to show detailed investigation streams
- **Configurable** via command-line arguments

#### Usage:

**Interactive Demo (recommended for presentations):**
```bash
python demo/run_demo.py
```
This mode pauses between scenarios, allowing the presenter to explain what's happening.

**Automated Demo:**
```bash
python demo/run_demo.py --auto
```
Automatically advances through all scenarios with timed pauses.

**Verbose Mode:**
```bash
python demo/run_demo.py --verbose
```
Shows detailed investigation stream output including all reasoning steps and tool calls.

**Custom Configuration:**
```bash
# Use a different model
python demo/run_demo.py --model us.amazon.nova-pro-v1:0

# Use a different region
python demo/run_demo.py --region us-east-1

# Load from config file
python demo/run_demo.py --config config.yaml
```

**Combined Options:**
```bash
python demo/run_demo.py --verbose --auto --model us.amazon.nova-pro-v1:0
```

## Demo Scenarios

The automated demo includes the following scenarios:

1. **Data Analysis: On-Time Performance**
   - Single-domain routing to Data Analyst
   - Demonstrates statistical analysis and KPI calculations

2. **Machine Learning: Delay Prediction**
   - Single-domain routing to ML Engineer
   - Shows model recommendations and code generation

3. **Visualization: Delay Distribution**
   - Single-domain routing to Visualization Expert
   - Demonstrates chart creation and specification output

4. **Multi-Domain: Comprehensive Delay Analysis**
   - Routes to all three specialists sequentially
   - Showcases the star topology architecture
   - Demonstrates response synthesis

5. **Multi-Domain: Load Factor Optimization**
   - Another multi-specialist coordination example
   - Shows context passing between agents

6. **Investigation Stream: Verbose Mode**
   - Highlights the investigation stream capabilities
   - Shows real-time reasoning and tool invocations

## Prerequisites

Before running the demo, ensure you have:

1. **AWS Credentials configured** for Amazon Bedrock access
2. **Required packages installed**: `pip install -r requirements.txt`
3. **Sample data generated**: Run `python src/data/generate_sample_data.py` if not already done
4. **Environment variables set** (optional):
   - `AWS_REGION` or `DS_STAR_REGION`
   - `DS_STAR_MODEL_ID` (default: us.amazon.nova-lite-v1:0)

## Tips for Presenters

### Before the Demo:
- Test the demo script beforehand to ensure credentials work
- Review `sample_queries.md` to understand routing behavior
- Prepare talking points for each scenario
- Consider running in verbose mode to show investigation details

### During the Demo:
- Use interactive mode to control pacing
- Explain the star topology when showing multi-domain queries
- Highlight the investigation stream output
- Point out response synthesis from multiple specialists
- Show the chart specification JSON output

### Key Points to Emphasize:
- **Star Topology**: Central orchestrator coordinates all specialists
- **Intelligent Routing**: Automatic query analysis and specialist selection
- **Context Sharing**: Conversation history flows between agents
- **Transparency**: Investigation stream shows all reasoning steps
- **Extensibility**: Easy to add new specialist agents

## Troubleshooting

**"Error: strands-agents package not installed"**
- Run: `pip install strands-agents strands-agents-tools`

**"Failed to validate AWS Bedrock credentials"**
- Ensure AWS credentials are configured
- Check that your region supports Amazon Nova models
- Verify IAM permissions for Bedrock access

**"FileNotFoundError: data/airline_operations.csv"**
- Generate sample data: `python src/data/generate_sample_data.py`

**Demo runs too fast in auto mode**
- Adjust pause durations in the scenario definitions
- Use interactive mode instead for better control

## Customizing the Demo

To add your own scenarios, edit `run_demo.py` and modify the `_create_scenarios()` method:

```python
DemoScenario(
    title="Your Scenario Title",
    query="Your query here",
    explanation="Presenter notes and what to watch for",
    expected_routing=["data_analyst"],  # or multiple specialists
    pause_duration=5.0  # seconds
)
```

## Additional Resources

- **Requirements**: `.kiro/specs/ds-star-multi-agent/requirements.md`
- **Design Document**: `.kiro/specs/ds-star-multi-agent/design.md`
- **Implementation Tasks**: `.kiro/specs/ds-star-multi-agent/tasks.md`
- **Main CLI**: `src/main.py` for interactive usage
