# DS-Star Multi-Agent System

Implementation of Google's DS-Star (Data Science Star) multi-agent framework using the AWS Strands Agents SDK. Supports both local Ollama models (default) and Amazon Bedrock.

## Overview

This system implements a star topology where a central Orchestrator Agent coordinates three specialist agents to solve complex data science queries:

- **Data Analyst Agent**: Handles data exploration, statistical analysis, and KPI calculations on airline operations data
- **ML Engineer Agent**: Provides machine learning recommendations, model selection guidance, and code generation
- **Visualization Expert Agent**: Creates charts and visualizations with dual output formats (matplotlib + Plotly JSON)

Key features:
- **Real-time investigation streaming**: See all reasoning steps, tool calls, and intermediate results
- **Multi-domain query handling**: Automatically routes queries to multiple specialists when needed
- **Chart-ready JSON output**: Structured chart specifications for UI integration
- **Conversation context**: Maintains history across multi-turn interactions
- **Robust error handling**: Automatic retries with exponential backoff for API failures

## Project Structure

```
ds-star-multi-agent/
├── src/
│   ├── agents/
│   │   ├── specialists/     # Specialist agent implementations
│   │   └── orchestrator.py  # Central orchestrator agent
│   ├── handlers/            # Stream and chart output handlers
│   ├── data/                # Data loading and management
│   ├── config.py            # Configuration management
│   ├── models.py            # Response data models
│   └── main.py              # CLI entry point
├── tests/                   # Test suite
├── data/                    # Sample airline operations data
├── output/                  # Generated chart specifications
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Package configuration
└── .env.example            # Environment variable template
```

## Data Models

The system uses structured dataclasses for type-safe response handling:

### ToolCall
Represents a single tool invocation with execution metadata:
- `tool_name`: Name of the invoked tool
- `inputs`: Input parameters dictionary
- `output`: Tool execution result
- `duration_ms`: Execution time in milliseconds

### SpecialistResponse
Response from a specialist agent:
- `agent_name`: Specialist identifier (e.g., "data_analyst")
- `query`: The processed query
- `response`: Agent's response text
- `tool_calls`: List of ToolCall objects
- `execution_time_ms`: Total execution time

### AgentResponse
Complete orchestrator response:
- `query`: Original user query
- `routing`: List of invoked specialist names
- `specialist_responses`: List of SpecialistResponse objects
- `synthesized_response`: Final combined response
- `charts`: List of chart specifications (if any)
- `total_time_ms`: Total processing time

All models support JSON serialization via `to_json()` and `to_dict()` methods for logging and debugging.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `strands-agents` - AWS Strands Agents SDK
- `strands-agents-tools` - Tool utilities for agents
- `pandas` - Data analysis
- `matplotlib` - Visualization
- `plotly` - Interactive charts
- `pyyaml` - Configuration file support
- `hypothesis` - Property-based testing
- `pytest` - Testing framework

### 2. Generate Sample Data

Create the airline operations dataset:

```bash
python src/data/generate_sample_data.py
```

This generates `data/airline_operations.csv` with 1000+ flight records including:
- Multiple airlines (AA, UA, DL, SW, JB)
- Various routes and time periods
- KPIs: on-time performance, delay causes, load factor, turnaround time, cancellations

### 3. Configure Model Provider

The system supports two model providers:

- **Ollama** (default): Run models locally using [Ollama](https://ollama.ai/)
- **Bedrock**: Use Amazon Bedrock with AWS credentials

#### Option A: Local Ollama (Default)

1. Install Ollama from https://ollama.ai/
2. Pull a model (e.g., Gemma 3 4B - default, faster on CPU):
   ```bash
   ollama pull gemma3:4b
   ```
   Or for better quality with more resources:
   ```bash
   ollama pull gemma3:27b
   ```
3. Start Ollama server (usually runs automatically)
4. Run DS-Star - it will use Ollama by default

#### Option B: Amazon Bedrock

Configure AWS credentials and set the model provider:

```bash
cp .env.example .env
# Edit .env with your credentials
```

Set `DS_STAR_MODEL_PROVIDER=bedrock` and configure AWS credentials.

#### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DS_STAR_MODEL_PROVIDER` | `ollama` | Model provider: `ollama` or `bedrock` |
| `DS_STAR_MODEL_ID` | `gemma3:4b` | Model identifier (e.g., `gemma3:4b` for Ollama, `us.amazon.nova-lite-v1:0` for Bedrock) |
| `DS_STAR_OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `AWS_REGION` | `us-west-2` | AWS region for Bedrock |
| `DS_STAR_VERBOSE` | `false` | Enable verbose mode |
| `DS_STAR_MAX_TOKENS` | `4096` | Maximum tokens for responses |
| `DS_STAR_TEMPERATURE` | `0.3` | Model temperature (0.0-1.0) |
| `DS_STAR_OUTPUT_DIR` | `./output` | Output directory for charts |
| `DS_STAR_DATA_PATH` | `./data/airline_operations.csv` | Path to dataset |
| `DS_STAR_RETRY_ATTEMPTS` | `3` | Retry attempts for API failures |
| `DS_STAR_RETRY_DELAY_BASE` | `1.0` | Base delay for exponential backoff |

#### Configuration File

Create a `config.yaml` or `config.json` file:

```yaml
# config.yaml - Using Ollama (default)
model_provider: ollama
model_id: gemma3:4b  # Use gemma3:27b for better quality
ollama_host: http://localhost:11434
verbose: false
max_tokens: 4096
temperature: 0.3
output_dir: ./output
data_path: ./data/airline_operations.csv
```

```yaml
# config.yaml - Using Bedrock
model_provider: bedrock
model_id: us.amazon.nova-lite-v1:0
region: us-west-2
verbose: false
max_tokens: 4096
temperature: 0.3
output_dir: ./output
data_path: ./data/airline_operations.csv
```

Then run with: `python src/main.py --config config.yaml`

**Configuration Precedence**: Environment variables override config file values, which override defaults.

## Usage

### Interactive CLI

Start the interactive command-line interface:

```bash
python src/main.py
```

The system will:
1. Validate configuration and model provider connection (Ollama or Bedrock)
2. Initialize the model and specialist agents
3. Display a ready prompt for queries

Example session:

```
DS-Star> Calculate the on-time performance for each airline
[Orchestrator] Routing query to: Data Analyst
[Data Analyst] Analyzing airline OTP data...
[Tool Call] query_airline_data(...)
[Result] AA: 82.3%, UA: 79.1%, DL: 85.7%, SW: 81.2%, JB: 78.9%

DS-Star> Now create a chart showing these results
[Orchestrator] Routing query to: Visualization Expert
[Visualization Expert] Creating bar chart...
[Chart Saved] output/otp_comparison.json
```

### Command-Line Options

```bash
# Use verbose mode to see detailed investigation stream
python src/main.py --verbose

# Use a specific configuration file
python src/main.py --config config.yaml

# Use a different model (Ollama)
python src/main.py --model gemma3:27b

# Use Bedrock instead of Ollama
python src/main.py --provider bedrock --model us.amazon.nova-lite-v1:0

# Use a different region
python src/main.py --region us-east-1

# Combine options
python src/main.py --verbose --config config.yaml
```

### Running the Demo

For presentations and demonstrations, use the automated demo script:

```bash
# Interactive demo (pauses between scenarios)
python demo/run_demo.py

# Automated demo (auto-advances)
python demo/run_demo.py --auto

# Verbose mode (shows investigation stream)
python demo/run_demo.py --verbose

# Combined options
python demo/run_demo.py --verbose --auto
```

See `demo/README.md` for detailed demo documentation and `demo/sample_queries.md` for example queries.

## Frontend UI

The system includes a modern React-based Investigation Workbench for interactive data science exploration.

### Features

- **Investigation Workflow**: Start with a hypothesis (e.g., "Why is On-Time Performance signaling?") and iteratively explore
- **Step-by-Step Analysis**: Each analysis step shows generated code, formatted responses, and visualizations
- **Interactive Charts**: Plotly-based charts with zoom, pan, and export capabilities
- **Approve/Decline Flow**: Review each step's results and either approve to continue or decline with feedback for refinement
- **Step Navigation**: Slider to navigate between investigation steps and track progress
- **Notes & Analysis**: Running notes panel with final analysis and conclusion fields
- **Real-time Streaming**: WebSocket-based updates show analysis progress in real-time

### Running the Frontend

```bash
# Terminal 1: Start the backend
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000

# Terminal 2: Start the frontend
cd frontend
npm install  # First time only
npm run dev
```

Open http://localhost:3000 to access the Investigation Workbench.

### Frontend Tech Stack

- **React 18** with TypeScript
- **Tailwind CSS v4** for styling
- **Plotly.js** for interactive charts
- **React Markdown** for formatted agent responses
- **Lucide React** for icons
- **WebSocket** for real-time updates

## Web API

The system includes a FastAPI-based web server for programmatic access and frontend integration.

### Starting the API Server

```bash
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000
```

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/status` | GET | System status with dataset info |
| `/api/query` | POST | Process a query (synchronous) |
| `/api/history` | GET | Get conversation history |
| `/api/history` | DELETE | Clear conversation history |

### API Response Models

**GET /api/status** returns:
```json
{
  "status": "ready",
  "model": "us.amazon.nova-lite-v1:0",
  "region": "us-west-2",
  "specialists": ["data_analyst", "ml_engineer", "visualization_expert"],
  "data_loaded": true,
  "dataset_info": {
    "filename": "airline_operations.csv",
    "description": "Airline operational data...",
    "columns": [{"name": "flight_id", "dtype": "int64"}, ...],
    "rowCount": 1000
  }
}
```

**POST /api/query** accepts:
```json
{
  "query": "Calculate on-time performance by airline",
  "context": {}
}
```

### WebSocket Streaming

Connect to `/ws/query` for real-time streaming of agent reasoning, tool calls, and results. Events include: `query_start`, `agent_start`, `routing`, `tool_start`, `tool_end`, `agent_end`, `response`, `error`.

### WebSocket Workbench Streaming

Connect to `/ws/stream` for the Investigation Workbench UI with iterative analysis workflow:

**Client → Server Events:**
| Event | Description |
|-------|-------------|
| `start_analysis` | Start a new analysis with `research_goal` |
| `approve_step` | Approve a step and continue to next |
| `refine_step` | Request refinement with feedback |

**Server → Client Events:**
| Event | Description |
|-------|-------------|
| `analysis_started` | Analysis initialized with ID |
| `step_started` | New step began |
| `iteration_started` | New iteration within a step |
| `code_generated` | Python code generated for analysis |
| `execution_complete` | Code execution finished with output |
| `visualization_ready` | Chart data ready for display |
| `verification_complete` | Verifier assessment complete |
| `step_completed` | Step finished |
| `step_approved` | Step was approved by user |
| `refinement_started` | Refinement iteration began |
| `analysis_completed` | Full analysis workflow complete |
| `error` | Error occurred during processing |

## Architecture

The system follows the DS-Star star topology pattern:

```
User Query
    ↓
Orchestrator Agent (Central Hub)
    ↓
    ├─→ Data Analyst Agent
    ├─→ ML Engineer Agent
    └─→ Visualization Expert Agent
    ↓
Synthesized Response
```

### Components

- **Orchestrator Agent** (`src/agents/orchestrator.py`): Central coordinator that analyzes queries, routes to specialists, and synthesizes responses
- **Specialist Agents** (`src/agents/specialists/`): Domain experts wrapped as tools using the Agent-as-Tool pattern
- **Investigation Stream Handler** (`src/handlers/stream_handler.py`): Real-time streaming of reasoning steps and tool calls
- **Chart Output Handler** (`src/handlers/chart_handler.py`): Generates structured chart specifications in JSON format
- **Configuration Module** (`src/config.py`): Flexible configuration with environment variables and file support
- **Error Handlers** (`src/handlers/`): Retry logic with exponential backoff and graceful error handling

## Example Queries

### Single-Domain Queries

**Data Analysis:**
```
Calculate the average delay time by airline and identify the worst performers
```

**Machine Learning:**
```
I want to predict flight delays. What model should I use and how do I implement it?
```

**Visualization:**
```
Create a chart showing the distribution of delay causes across all flights
```

### Multi-Domain Queries

**Comprehensive Analysis:**
```
Analyze delay patterns, recommend a prediction model, and create visualizations
```

This query automatically routes to all three specialists in sequence, with the Orchestrator synthesizing their responses into a cohesive answer.

See `demo/sample_queries.md` for more examples with expected routing behavior.

## Requirements

- Python >= 3.9
- One of the following model providers:
  - **Ollama** (default): Local installation of [Ollama](https://ollama.ai/) with a compatible model (e.g., `gemma3:27b`)
  - **Bedrock**: AWS Bedrock access with Amazon Nova Lite model and configured AWS credentials
- See `requirements.txt` for full dependency list

## Testing

The system uses both unit tests and property-based tests for comprehensive coverage.

### Test Configuration

The test suite uses a mock configuration (`tests/conftest.py`) that allows tests to run without requiring AWS Bedrock credentials or the full Strands SDK installation. The mock system:

- **Mocks the Strands SDK**: Provides lightweight mocks for `strands`, `strands_bedrock`, and `strands_agents` modules
- **Passthrough tool decorator**: The `@tool` decorator is mocked to return functions unchanged, allowing specialist agents to be tested as regular Python functions
- **Module cleanup**: Automatically removes and re-mocks modules before test collection to ensure clean test isolation
- **No external dependencies**: Tests can run in CI/CD environments without AWS credentials

The mock configuration is automatically applied via pytest hooks, so no additional setup is needed to run tests.

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Property-based tests only
pytest tests/property/

# Integration tests
pytest tests/integration/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html
```

### Property-Based Testing

The system includes property-based tests using the `hypothesis` framework to verify universal properties across all inputs. Each property test runs a minimum of 100 iterations with randomly generated inputs.

Example properties tested:
- Query routing correctness
- Response structure validation
- Code generation validity
- Configuration loading precedence
- Chart specification structure

### Testing Without AWS Credentials

All tests are designed to run without AWS Bedrock access. The mock configuration in `conftest.py` intercepts Strands SDK imports and provides test doubles that simulate the SDK behavior without making actual API calls. This enables:

- Fast test execution (no network calls)
- Reliable CI/CD pipelines (no credential management)
- Local development without AWS setup
- Isolated unit testing of business logic

## Troubleshooting

**"Error: strands-agents package not installed"**
```bash
pip install strands-agents strands-agents-tools ollama
```

**"Failed to connect to Ollama"**
- Ensure Ollama is installed and running (`ollama serve`)
- Verify the model is pulled (`ollama pull gemma3:27b`)
- Check `DS_STAR_OLLAMA_HOST` if using a non-default URL

**"Failed to validate AWS Bedrock credentials"** (when using Bedrock)
- Ensure AWS credentials are configured
- Verify your region supports Amazon Nova models
- Check IAM permissions for Bedrock access

**"FileNotFoundError: data/airline_operations.csv"**
```bash
python src/data/generate_sample_data.py
```

**"Token limit exceeded"**
- Reduce `max_tokens` in configuration
- The system automatically truncates conversation history to fit limits

## Project Structure

```
ds-star-multi-agent/
├── .kiro/
│   └── specs/                    # Requirements, design, and tasks
├── src/
│   ├── agents/
│   │   ├── specialists/          # Specialist agent implementations
│   │   │   ├── data_analyst.py
│   │   │   ├── ml_engineer.py
│   │   │   └── visualization_expert.py
│   │   └── orchestrator.py       # Central orchestrator agent
│   ├── handlers/
│   │   ├── stream_handler.py     # Investigation stream handler
│   │   ├── chart_handler.py      # Chart output handler
│   │   ├── retry_handler.py      # Retry logic with backoff
│   │   └── error_handler.py      # Error handling utilities
│   ├── data/
│   │   ├── airline_data.py       # Data loader and tools
│   │   └── generate_sample_data.py  # Sample data generator
│   ├── config.py                 # Configuration management
│   ├── models.py                 # Response data models
│   └── main.py                   # CLI entry point
├── tests/
│   ├── unit/                     # Unit tests
│   ├── property/                 # Property-based tests
│   └── integration/              # Integration tests
├── demo/
│   ├── run_demo.py              # Automated demo script
│   ├── sample_queries.md        # Example queries
│   └── README.md                # Demo documentation
├── data/
│   └── airline_operations.csv   # Sample dataset (generated)
├── output/                      # Chart specifications (generated)
├── requirements.txt             # Python dependencies
├── pyproject.toml              # Package configuration
└── .env.example                # Environment variable template
```

## Contributing

See `.kiro/specs/ds-star-multi-agent/` for detailed requirements, design documentation, and implementation tasks.

## License

[Add license information]
