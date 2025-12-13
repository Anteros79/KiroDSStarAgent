# Implementation Plan

- [x] 1. Set up project structure and dependencies
  - Create directory structure: `src/`, `src/agents/`, `src/agents/specialists/`, `src/handlers/`, `src/data/`, `tests/`, `output/`
  - Create `requirements.txt` with: `strands-agents`, `strands-agents-tools`, `pandas`, `matplotlib`, `plotly`, `hypothesis`, `pytest`
  - Create `pyproject.toml` or `setup.py` for package configuration
  - Create `.env.example` with required environment variables (AWS_BEDROCK_API_KEY, AWS_REGION)
  - _Requirements: 1.1, 1.2, 9.1_

- [x] 2. Implement configuration module
  - [x] 2.1 Create Config dataclass with all settings
    - Implement `src/config.py` with Config dataclass
    - Add fields: model_id, region, verbose, max_tokens, temperature, output_dir, data_path, retry_attempts, retry_delay_base
    - Set Nova Lite as default: `us.amazon.nova-lite-v1:0`
    - _Requirements: 9.1, 9.3, 9.4_
  - [x] 2.2 Implement config loading from environment and file
    - Add `from_env()` classmethod to load from environment variables
    - Add `from_file()` classmethod to load from JSON/YAML config file
    - Implement precedence: env vars override file values
    - Add validation and default fallback with warning logging
    - _Requirements: 9.1, 9.4_
  - [ ]* 2.3 Write property tests for configuration
    - **Property 13: Configuration Loading**
    - **Property 16: Configuration Defaults**
    - **Validates: Requirements 9.1, 9.4**

- [x] 3. Implement investigation stream handler
  - [x] 3.1 Create InvestigationStreamHandler class
    - Implement `src/handlers/stream_handler.py`
    - Extend Strands CallbackHandler base class
    - Implement event methods: on_agent_start, on_routing_decision, on_tool_start, on_tool_end, on_agent_end, on_error
    - Add verbose mode toggle for detailed vs. summary output
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 11.1, 11.2, 11.3, 11.4_
  - [ ]* 3.2 Write property tests for stream handler
    - **Property 9: Investigation Stream Completeness**
    - **Property 14: Verbose Mode Output**
    - **Validates: Requirements 7.1-7.4, 11.1-11.4, 9.2**

- [x] 4. Implement airline data module
  - [x] 4.1 Create sample airline operations dataset
    - Create `src/data/generate_sample_data.py` script
    - Generate 1000+ flight records with realistic distributions
    - Include all KPIs: OTP, delay causes, load factor, turnaround, cancellations
    - Include multiple airlines (AA, UA, DL, SW, JB), routes, and date range
    - Save to `data/airline_operations.csv`
    - _Requirements: 10.1, 10.2, 10.3_
  - [x] 4.2 Create AirlineDataLoader class
    - Implement `src/data/airline_data.py`
    - Add load(), get_schema(), get_sample() methods
    - Implement schema validation on load
    - _Requirements: 10.1, 10.2, 10.3_
  - [x] 4.3 Create query_airline_data tool
    - Implement @tool decorated function for pandas operations
    - Include docstring with available columns for LLM context
    - _Requirements: 10.4, 3.1_
  - [ ]* 4.4 Write property tests for data module
    - **Property 17: Dataset Schema Validation**
    - **Validates: Requirements 10.2, 10.3**

- [x] 5. Implement response models
  - [x] 5.1 Create response dataclasses
    - Implement `src/models.py`
    - Define SpecialistResponse, AgentResponse, ToolCall dataclasses
    - Add serialization methods for JSON output
    - _Requirements: 3.4, 4.4, 5.4, 2.4_

- [x] 6. Implement chart output handler
  - [x] 6.1 Create ChartSpecification dataclass
    - Implement `src/handlers/chart_handler.py`
    - Define ChartSpecification with: chart_type, title, data, x_axis, y_axis, styling, plotly_json, matplotlib_code
    - Define AxisConfig dataclass for axis configuration
    - _Requirements: 12.1, 12.2_
  - [x] 6.2 Create ChartOutputHandler class
    - Implement save_chart_spec() to write JSON to output directory
    - Implement generate_plotly_json() for web-ready format
    - _Requirements: 12.3, 12.4_
  - [ ]* 6.3 Write property tests for chart handler
    - **Property 18: Chart Specification Structure**
    - **Property 19: Dual Chart Format Output**
    - **Property 20: Chart File Persistence**
    - **Validates: Requirements 12.1, 12.2, 12.3, 12.4**

- [x] 7. Implement specialist agents
  - [x] 7.1 Create Data Analyst Agent
    - Implement `src/agents/specialists/data_analyst.py`
    - Create @tool decorated data_analyst function
    - Configure with pandas analysis system prompt
    - Include query_airline_data tool
    - Return structured SpecialistResponse
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  - [x] 7.2 Create ML Engineer Agent
    - Implement `src/agents/specialists/ml_engineer.py`
    - Create @tool decorated ml_engineer function
    - Configure with ML recommendation system prompt
    - Include python_repl tool for code generation
    - Return structured SpecialistResponse
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  - [x] 7.3 Create Visualization Agent
    - Implement `src/agents/specialists/visualization_expert.py`
    - Create @tool decorated visualization_expert function
    - Configure with visualization system prompt
    - Include chart output handler integration
    - Generate both matplotlib code and Plotly JSON
    - Return structured SpecialistResponse
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 12.1, 12.2, 12.3_
  - [ ]* 7.4 Write property tests for specialist agents
    - **Property 5: Specialist Response Structure**
    - **Property 6: Code Generation Validity**
    - **Validates: Requirements 3.4, 4.3, 4.4, 5.2, 5.4**

- [x] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Implement Orchestrator Agent
  - [x] 9.1 Create OrchestratorAgent class
    - Implement `src/agents/orchestrator.py`
    - Initialize with BedrockModel (Nova Lite), specialist tools, stream handler
    - Create orchestrator system prompt with routing instructions
    - _Requirements: 2.1, 2.2_
  - [x] 9.2 Implement query routing logic
    - Add _route_query() method for intent analysis
    - Support single and multi-domain routing
    - Pass context to specialists via invocation_state
    - _Requirements: 2.1, 2.2, 2.3_
  - [x] 9.3 Implement response synthesis
    - Add _synthesize_responses() method
    - Combine specialist responses with attribution
    - Include chart specifications in final response
    - _Requirements: 2.4, 7.4_
  - [x] 9.4 Implement conversation history management
    - Add context tracking across turns
    - Implement token-aware truncation
    - _Requirements: 6.1, 6.2, 6.3_
  - [ ]* 9.5 Write property tests for orchestrator
    - **Property 1: Query Routing Correctness**
    - **Property 2: Multi-Domain Query Handling**
    - **Property 3: Context Propagation to Specialists**
    - **Property 4: Response Synthesis Completeness**
    - **Property 7: Conversation History Maintenance**
    - **Property 8: Context Size Management**
    - **Property 12: Token Limit Truncation**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 6.1, 6.2, 6.3**

- [x] 10. Implement error handling
  - [x] 10.1 Create BedrockRetryHandler
    - Implement `src/handlers/retry_handler.py`
    - Add exponential backoff logic (delay = base * 2^attempt)
    - Configure max 3 retry attempts
    - _Requirements: 8.1_
  - [x] 10.2 Implement safe_specialist_call wrapper
    - Add error catching for specialist invocations
    - Return fallback response on error
    - Log error details
    - _Requirements: 8.2, 8.4_
  - [ ]* 10.3 Write property tests for error handling
    - **Property 10: Retry Logic Correctness**
    - **Property 11: Error Handling Fallback**
    - **Validates: Requirements 8.1, 8.2**

- [x] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Implement main CLI entry point
  - [x] 12.1 Create DSStarCLI class
    - Implement `src/main.py`
    - Add argument parsing for config options
    - Initialize all components (config, orchestrator, handlers)
    - _Requirements: 1.1, 1.4_
  - [x] 12.2 Implement interactive query loop
    - Add run() method with input prompt
    - Process queries through orchestrator
    - Display investigation stream and responses
    - Handle graceful shutdown (Ctrl+C)
    - _Requirements: 1.4, 2.1_
  - [x] 12.3 Implement startup validation
    - Validate Bedrock credentials on startup
    - Display connection status and ready message
    - Show clear error messages for credential issues
    - _Requirements: 1.2, 1.3_

- [x] 13. Create demo scenarios
  - [x] 13.1 Create sample queries file
    - Create `demo/sample_queries.md` with example queries for each specialist
    - Include multi-domain query examples
    - Add expected routing explanations
    - _Requirements: 10.4, 7.1_
  - [x] 13.2 Create demo script
    - Create `demo/run_demo.py` for automated demo walkthrough
    - Include pauses for presenter explanation
    - Show investigation stream highlights
    - _Requirements: 7.1, 7.2, 11.1_

- [x] 14. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Initialize data loader in main entry point



  - [x] 15.1 Add data loader initialization to DSStarCLI.initialize()


    - Import initialize_data_loader from src.data.airline_data
    - Call initialize_data_loader(config.data_path) during system initialization
    - Add error handling for missing or invalid data file
    - _Requirements: 10.1, 10.4_


- [x] 16. Generate sample dataset if missing

  - [x] 16.1 Add automatic dataset generation


    - Check if data file exists during initialization
    - If missing, automatically run generate_sample_data.py
    - Log dataset generation and provide user feedback
    - _Requirements: 10.1, 10.2, 10.3_






- [x] 17. Future Enhancement: Additional Specialist Agents (Optional)


  - [ ] 17.1 Create Data Engineer Agent placeholder
    - Implement `src/agents/specialists/data_engineer.py` stub


    - Add ETL and data transformation system prompt
    - _Requirements: 13.1_
  - [ ] 17.2 Create Statistics Expert Agent placeholder
    - Implement `src/agents/specialists/statistics_expert.py` stub
    - Add hypothesis testing system prompt
    - _Requirements: 13.2_
  - [ ] 17.3 Create Domain Expert Agent placeholder
    - Implement `src/agents/specialists/domain_expert.py` stub
    - Add airline industry knowledge system prompt
    - _Requirements: 13.3_
