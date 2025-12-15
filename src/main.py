"""Main CLI entry point for DS-Star multi-agent system.

This module provides the command-line interface for interacting with the
DS-Star multi-agent system. It handles initialization, configuration,
and the interactive query loop.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from src.config import Config
from src.agents.orchestrator import OrchestratorAgent
from src.handlers.stream_handler import InvestigationStreamHandler

# Import specialist agents
from src.agents.specialists.data_analyst import data_analyst
from src.agents.specialists.ml_engineer import ml_engineer
from src.agents.specialists.visualization_expert import visualization_expert

# Import data loader
from src.data.airline_data import initialize_data_loader

# Import Strands components
try:
    from strands.models.bedrock import BedrockModel
    from strands.models.ollama import OllamaModel
except ImportError:
    print("Error: strands-agents package not installed.")
    print("Please install with: pip install strands-agents strands-agents-tools ollama")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DSStarCLI:
    """Command-line interface for DS-Star multi-agent system.
    
    This class manages the lifecycle of the DS-Star system, including:
    - Configuration loading and validation
    - Component initialization (orchestrator, specialists, handlers)
    - Interactive query loop
    - Graceful shutdown
    
    Attributes:
        config: System configuration
        orchestrator: Central orchestrator agent
        stream_handler: Investigation stream handler
    """
    
    def __init__(self, config: Config):
        """Initialize the DS-Star CLI.
        
        Args:
            config: System configuration
        """
        self.config = config
        self.orchestrator: Optional[OrchestratorAgent] = None
        self.stream_handler: Optional[InvestigationStreamHandler] = None
        
        # Set logging level based on verbose flag
        if config.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Verbose mode enabled")
    
    def initialize(self) -> bool:
        """Initialize all system components.
        
        This method:
        1. Validates configuration
        2. Creates output directory
        3. Initializes the Bedrock model
        4. Creates specialist agents
        5. Initializes the orchestrator
        6. Sets up the stream handler
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing DS-Star multi-agent system...")
            
            # Validate configuration
            self.config.validate()
            logger.info(f"Configuration validated: model={self.config.model_id}, region={self.config.region}")
            
            # Create output directory if it doesn't exist
            output_path = Path(self.config.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Output directory: {output_path.absolute()}")
            
            # Initialize data loader
            logger.info("Loading airline operations dataset...")
            
            # Check if data file exists, generate if missing
            data_file_path = Path(self.config.data_path)
            if not data_file_path.exists():
                logger.warning(f"Data file not found: {self.config.data_path}")
                logger.info("Generating sample airline operations dataset...")
                try:
                    from src.data.generate_sample_data import generate_dataset, save_to_csv
                    
                    # Generate sample dataset
                    records = generate_dataset(num_records=1200)
                    save_to_csv(records, self.config.data_path)
                    
                    logger.info(f"✓ Generated {len(records)} flight records")
                    logger.info(f"✓ Sample dataset saved to {self.config.data_path}")
                except Exception as gen_error:
                    logger.error(f"✗ Failed to generate sample dataset: {gen_error}")
                    raise ValueError(f"Failed to generate sample dataset: {gen_error}") from gen_error
            
            try:
                initialize_data_loader(self.config.data_path)
                logger.info(f"✓ Airline data loaded from {self.config.data_path}")
            except ValueError as e:
                logger.error(f"✗ Invalid data file: {e}")
                logger.error("The data file does not have the expected schema.")
                raise ValueError(f"Invalid data file: {e}") from e
            except Exception as e:
                logger.error(f"✗ Error loading data: {e}")
                raise ValueError(f"Error loading data: {e}") from e
            
            # Initialize stream handler
            self.stream_handler = InvestigationStreamHandler(verbose=self.config.verbose)
            logger.info("Investigation stream handler initialized")
            
            # Initialize model based on provider
            if self.config.model_provider == "ollama":
                logger.info(f"Connecting to Ollama at {self.config.ollama_host}...")
                model = OllamaModel(
                    model_id=self.config.model_id,
                    host=self.config.ollama_host,
                )
                logger.info(f"Ollama model initialized: {self.config.model_id}")
            else:
                logger.info("Connecting to Amazon Bedrock...")
                model = BedrockModel(
                    model_id=self.config.model_id,
                    region=self.config.region,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature
                )
                logger.info(f"Bedrock model initialized: {self.config.model_id}")
            
            # Create specialist agents dictionary
            specialists = {
                "data_analyst": data_analyst,
                "ml_engineer": ml_engineer,
                "visualization_expert": visualization_expert
            }
            logger.info(f"Loaded {len(specialists)} specialist agents")
            
            # Initialize orchestrator
            self.orchestrator = OrchestratorAgent(
                model=model,
                specialists=specialists,
                stream_handler=self.stream_handler,
                config=self.config
            )
            logger.info("Orchestrator agent initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            return False

    def validate_credentials(self) -> bool:
        """Validate Amazon Bedrock credentials on startup.
        
        This method attempts to verify that the AWS credentials are valid
        and that the Bedrock service is accessible.
        
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            if self.config.model_provider == "ollama":
                logger.info(f"Validating Ollama connection at {self.config.ollama_host}...")
                # For Ollama, just try to create the model - it will fail if server is not running
                test_model = OllamaModel(
                    model_id=self.config.model_id,
                    host=self.config.ollama_host,
                )
                logger.info("✓ Ollama connection validated successfully")
                return True
            else:
                logger.info("Validating Amazon Bedrock credentials...")
                
                # Check for required environment variables
                aws_region = os.getenv("AWS_REGION") or os.getenv("DS_STAR_REGION")
                
                if not aws_region:
                    logger.warning("AWS_REGION not set, using default from config")
                
                # Try to create a test model instance to validate credentials
                test_model = BedrockModel(
                    model_id=self.config.model_id,
                    region=self.config.region,
                    max_tokens=100,
                    temperature=0.3
                )
                
                logger.info("✓ Bedrock credentials validated successfully")
                return True
            
        except Exception as e:
            logger.error(f"✗ Credential validation failed: {e}")
            if self.config.model_provider == "ollama":
                logger.error("Please ensure Ollama is running and the model is available.")
                logger.error(f"  1. Start Ollama: ollama serve")
                logger.error(f"  2. Pull model: ollama pull {self.config.model_id}")
            else:
                logger.error("Please ensure you have valid AWS credentials configured.")
                logger.error("You can set credentials via:")
                logger.error("  1. Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
                logger.error("  2. AWS credentials file: ~/.aws/credentials")
                logger.error("  3. IAM role (if running on AWS)")
            return False
    
    def display_welcome(self) -> None:
        """Display welcome message and system information."""
        print("\n" + "=" * 70)
        print("  DS-Star Multi-Agent System")
        print("  Powered by Amazon Nova Lite via AWS Bedrock")
        print("=" * 70)
        print(f"\nConfiguration:")
        print(f"  Model: {self.config.model_id}")
        print(f"  Region: {self.config.region}")
        print(f"  Verbose: {self.config.verbose}")
        print(f"  Output Directory: {self.config.output_dir}")
        print(f"  Data Path: {self.config.data_path}")
        print(f"\nAvailable Specialists:")
        print("  • Data Analyst - Statistical analysis and data exploration")
        print("  • ML Engineer - Machine learning recommendations and code generation")
        print("  • Visualization Expert - Chart creation and visualization guidance")
        print(f"\n{'=' * 70}")
        print("\nType your query or 'help' for assistance, 'quit' to exit.\n")
    
    def display_help(self) -> None:
        """Display help information."""
        print("\n" + "=" * 70)
        print("  DS-Star Help")
        print("=" * 70)
        print("\nCommands:")
        print("  help     - Display this help message")
        print("  quit     - Exit the system")
        print("  exit     - Exit the system")
        print("  clear    - Clear conversation history")
        print("  history  - Show conversation history summary")
        print("\nExample Queries:")
        print("  • What's the average delay by airline?")
        print("  • Analyze on-time performance trends")
        print("  • Build a model to predict flight delays")
        print("  • Create a bar chart showing delays by airline")
        print("  • Compare load factors across different routes")
        print(f"\n{'=' * 70}\n")
    
    def process_query(self, query: str) -> Optional[str]:
        """Process a user query through the orchestrator.
        
        Args:
            query: The user's natural language query
        
        Returns:
            The synthesized response, or None if processing failed
        """
        if not self.orchestrator:
            logger.error("Orchestrator not initialized")
            return None
        
        try:
            # Reset stream handler for new query
            self.stream_handler.reset()
            
            # Add context for specialists
            context = {
                "output_dir": self.config.output_dir,
                "data_path": self.config.data_path
            }
            
            # Process through orchestrator
            response = self.orchestrator.process(query, context)
            
            return response.synthesized_response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return f"I encountered an error processing your query: {str(e)}"

    def run(self) -> None:
        """Run the interactive query loop.
        
        This method implements the main interaction loop where users can
        submit queries and receive responses. It handles:
        - User input
        - Command processing (help, quit, clear, history)
        - Query processing through the orchestrator
        - Response display
        - Graceful shutdown on Ctrl+C
        """
        try:
            # Display welcome message
            self.display_welcome()
            
            # Main interaction loop
            while True:
                try:
                    # Get user input
                    user_input = input("You: ").strip()
                    
                    # Skip empty input
                    if not user_input:
                        continue
                    
                    # Handle commands
                    if user_input.lower() in ["quit", "exit"]:
                        print("\nThank you for using DS-Star. Goodbye!")
                        break
                    
                    elif user_input.lower() == "help":
                        self.display_help()
                        continue
                    
                    elif user_input.lower() == "clear":
                        if self.orchestrator:
                            self.orchestrator.clear_history()
                            print("\n✓ Conversation history cleared.\n")
                        continue
                    
                    elif user_input.lower() == "history":
                        if self.orchestrator:
                            summary = self.orchestrator.get_history_summary()
                            print(f"\nConversation History Summary:")
                            print(f"  Total turns: {summary['total_turns']}")
                            print(f"  Total entries: {summary['total_entries']}")
                            print(f"  Estimated tokens: {summary['estimated_tokens']} / {summary['max_tokens']}")
                            print()
                        continue
                    
                    # Process query
                    print()  # Add blank line before investigation stream
                    response = self.process_query(user_input)
                    
                    # Display response
                    if response:
                        print(f"\n{'=' * 70}")
                        print("DS-Star Response:")
                        print(f"{'=' * 70}\n")
                        print(response)
                        print(f"\n{'=' * 70}\n")
                    else:
                        print("\n✗ Failed to process query. Please try again.\n")
                
                except KeyboardInterrupt:
                    print("\n\nInterrupted by user. Type 'quit' to exit or press Ctrl+C again.")
                    try:
                        # Give user a chance to quit gracefully
                        continue
                    except KeyboardInterrupt:
                        print("\n\nShutting down...")
                        break
                
                except EOFError:
                    # Handle Ctrl+D
                    print("\n\nShutting down...")
                    break
        
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            print(f"\n✗ Fatal error: {e}")
        
        finally:
            self.shutdown()
    
    def shutdown(self) -> None:
        """Perform graceful shutdown.
        
        This method cleans up resources and logs shutdown information.
        """
        logger.info("Shutting down DS-Star system...")
        
        # Clear conversation history
        if self.orchestrator:
            self.orchestrator.clear_history()
        
        logger.info("Shutdown complete")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="DS-Star Multi-Agent System - AI-powered airline operations analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default configuration
  python -m src.main
  
  # Run with custom config file
  python -m src.main --config config.yaml
  
  # Run in verbose mode
  python -m src.main --verbose
  
  # Use a different model
  python -m src.main --model us.amazon.nova-pro-v1:0
  
Environment Variables:
  DS_STAR_MODEL_ID       - Bedrock model ID
  DS_STAR_REGION         - AWS region
  AWS_REGION             - AWS region (alternative)
  DS_STAR_VERBOSE        - Enable verbose mode (true/false)
  DS_STAR_OUTPUT_DIR     - Output directory path
  DS_STAR_DATA_PATH      - Data file path
        """
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (JSON or YAML)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        help="Bedrock model ID (default: us.amazon.nova-lite-v1:0)"
    )
    
    parser.add_argument(
        "--region",
        type=str,
        help="AWS region (default: us-west-2)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output with detailed investigation stream"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for charts and logs (default: ./output)"
    )
    
    parser.add_argument(
        "--data-path",
        type=str,
        help="Path to airline operations data (default: ./data/airline_operations.csv)"
    )
    
    return parser.parse_args()


def main() -> int:
    """Main entry point for the DS-Star CLI.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Parse command-line arguments
        args = parse_arguments()
        
        # Load configuration with precedence: CLI args > env vars > config file > defaults
        if args.config:
            config = Config.load(config_file=args.config)
        else:
            config = Config.load()
        
        # Override with CLI arguments if provided
        if args.model:
            config.model_id = args.model
        if args.region:
            config.region = args.region
        if args.verbose:
            config.verbose = True
        if args.output_dir:
            config.output_dir = args.output_dir
        if args.data_path:
            config.data_path = args.data_path
        
        # Create CLI instance
        cli = DSStarCLI(config)
        
        # Validate credentials
        if not cli.validate_credentials():
            print("\n✗ Failed to validate AWS Bedrock credentials.")
            print("Please configure your AWS credentials and try again.")
            return 1
        
        # Initialize system
        if not cli.initialize():
            print("\n✗ Failed to initialize DS-Star system.")
            return 1
        
        print("\n✓ DS-Star system ready!")
        
        # Run interactive loop
        cli.run()
        
        return 0
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        return 0
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n✗ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
