#!/usr/bin/env python3
"""Automated demo script for DS-Star multi-agent system.

This script provides an automated walkthrough of the DS-Star system's capabilities,
demonstrating query routing, specialist coordination, and investigation streaming.
Designed for presenter-led demonstrations with pauses for explanation.
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.agents.orchestrator import OrchestratorAgent
from src.handlers.stream_handler import InvestigationStreamHandler
from src.agents.specialists.data_analyst import data_analyst
from src.agents.specialists.ml_engineer import ml_engineer
from src.agents.specialists.visualization_expert import visualization_expert

try:
    from strands_bedrock import BedrockModel
except ImportError:
    print("Error: strands-agents package not installed.")
    print("Please install with: pip install strands-agents strands-agents-tools")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DemoScenario:
    """Represents a single demo scenario with query and explanation."""
    
    def __init__(
        self,
        title: str,
        query: str,
        explanation: str,
        expected_routing: List[str],
        pause_duration: float = 3.0
    ):
        """Initialize a demo scenario.
        
        Args:
            title: Scenario title for display
            query: The query to execute
            explanation: Explanation for the presenter
            expected_routing: Expected specialist routing
            pause_duration: Seconds to pause after scenario
        """
        self.title = title
        self.query = query
        self.explanation = explanation
        self.expected_routing = expected_routing
        self.pause_duration = pause_duration


class DSStarDemo:
    """Automated demo runner for DS-Star multi-agent system."""
    
    def __init__(self, config: Config, auto_advance: bool = False):
        """Initialize the demo runner.
        
        Args:
            config: System configuration
            auto_advance: If True, automatically advance between scenarios
        """
        self.config = config
        self.auto_advance = auto_advance
        self.orchestrator: Optional[OrchestratorAgent] = None
        self.stream_handler: Optional[InvestigationStreamHandler] = None
        
        # Define demo scenarios
        self.scenarios = self._create_scenarios()
    
    def _create_scenarios(self) -> List[DemoScenario]:
        """Create the list of demo scenarios.
        
        Returns:
            List of DemoScenario objects
        """
        return [
            DemoScenario(
                title="Data Analysis: On-Time Performance",
                query="Calculate the on-time performance rate for each airline. Which airline has the best OTP?",
                explanation=(
                    "This query demonstrates single-domain routing to the Data Analyst.\n"
                    "Watch for:\n"
                    "  • Query routing decision\n"
                    "  • Pandas operations on airline data\n"
                    "  • Statistical calculations\n"
                    "  • Structured response format"
                ),
                expected_routing=["data_analyst"],
                pause_duration=5.0
            ),
            
            DemoScenario(
                title="Machine Learning: Delay Prediction",
                query="I want to predict flight delays. What machine learning model should I use and how would I implement it?",
                explanation=(
                    "This query demonstrates routing to the ML Engineer specialist.\n"
                    "Watch for:\n"
                    "  • Model recommendations with trade-offs\n"
                    "  • Feature engineering suggestions\n"
                    "  • Generated scikit-learn code\n"
                    "  • Implementation guidance"
                ),
                expected_routing=["ml_engineer"],
                pause_duration=5.0
            ),
            
            DemoScenario(
                title="Visualization: Delay Distribution",
                query="Create a visualization showing the distribution of delay times across all flights.",
                explanation=(
                    "This query demonstrates routing to the Visualization Expert.\n"
                    "Watch for:\n"
                    "  • Chart type recommendation\n"
                    "  • Matplotlib/Plotly code generation\n"
                    "  • Chart specification JSON output\n"
                    "  • Styling and customization options"
                ),
                expected_routing=["visualization_expert"],
                pause_duration=5.0
            ),
            
            DemoScenario(
                title="Multi-Domain: Comprehensive Delay Analysis",
                query="Analyze the delay patterns in the data, recommend a model to predict delays, and create visualizations showing the key insights.",
                explanation=(
                    "This query demonstrates multi-domain routing across all specialists.\n"
                    "This is the STAR TOPOLOGY in action!\n"
                    "Watch for:\n"
                    "  • Sequential routing: Data Analyst → ML Engineer → Visualization Expert\n"
                    "  • Context passing between specialists\n"
                    "  • Response synthesis by the Orchestrator\n"
                    "  • Comprehensive multi-faceted answer"
                ),
                expected_routing=["data_analyst", "ml_engineer", "visualization_expert"],
                pause_duration=8.0
            ),
            
            DemoScenario(
                title="Multi-Domain: Load Factor Optimization",
                query="What routes have low load factors, what factors might predict load factor, and how can I visualize this to present to management?",
                explanation=(
                    "Another multi-domain query demonstrating specialist coordination.\n"
                    "Watch for:\n"
                    "  • Data analysis identifying low-performing routes\n"
                    "  • ML recommendations for predictive modeling\n"
                    "  • Executive-friendly visualization suggestions\n"
                    "  • Unified response synthesis"
                ),
                expected_routing=["data_analyst", "ml_engineer", "visualization_expert"],
                pause_duration=8.0
            ),
            
            DemoScenario(
                title="Investigation Stream: Verbose Mode",
                query="What are the most common delay causes and show me a chart of the results?",
                explanation=(
                    "This final scenario highlights the investigation stream in verbose mode.\n"
                    "Watch for:\n"
                    "  • Detailed reasoning steps\n"
                    "  • Tool invocation details\n"
                    "  • Intermediate results\n"
                    "  • Real-time streaming output"
                ),
                expected_routing=["data_analyst", "visualization_expert"],
                pause_duration=5.0
            )
        ]
    
    def initialize(self) -> bool:
        """Initialize the DS-Star system for demo.
        
        Returns:
            True if initialization successful
        """
        try:
            logger.info("Initializing DS-Star demo system...")
            
            # Validate configuration
            self.config.validate()
            
            # Create output directory
            output_path = Path(self.config.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize stream handler
            self.stream_handler = InvestigationStreamHandler(verbose=self.config.verbose)
            
            # Initialize Bedrock model
            model = BedrockModel(
                model_id=self.config.model_id,
                region=self.config.region,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            # Create specialists dictionary
            specialists = {
                "data_analyst": data_analyst,
                "ml_engineer": ml_engineer,
                "visualization_expert": visualization_expert
            }
            
            # Initialize orchestrator
            self.orchestrator = OrchestratorAgent(
                model=model,
                specialists=specialists,
                stream_handler=self.stream_handler,
                config=self.config
            )
            
            logger.info("Demo system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            return False
    
    def display_welcome(self) -> None:
        """Display welcome message for demo."""
        print("\n" + "=" * 80)
        print("  DS-STAR MULTI-AGENT SYSTEM - AUTOMATED DEMO")
        print("  Powered by Amazon Nova Lite via AWS Bedrock")
        print("=" * 80)
        print(f"\nConfiguration:")
        print(f"  Model: {self.config.model_id}")
        print(f"  Region: {self.config.region}")
        print(f"  Verbose Mode: {self.config.verbose}")
        print(f"  Scenarios: {len(self.scenarios)}")
        print(f"\nThis demo will showcase:")
        print("  • Single-domain query routing")
        print("  • Multi-domain specialist coordination")
        print("  • Star topology architecture")
        print("  • Investigation stream output")
        print("  • Response synthesis")
        print(f"\n{'=' * 80}\n")
    
    def display_scenario_header(self, scenario: DemoScenario, index: int) -> None:
        """Display scenario header with explanation.
        
        Args:
            scenario: The scenario to display
            index: Scenario number (1-indexed)
        """
        print("\n" + "=" * 80)
        print(f"  SCENARIO {index}/{len(self.scenarios)}: {scenario.title}")
        print("=" * 80)
        print(f"\nQuery: \"{scenario.query}\"")
        print(f"\nExpected Routing: {' → '.join(scenario.expected_routing)}")
        print(f"\nPresenter Notes:")
        print(scenario.explanation)
        print("\n" + "-" * 80)
        
        if not self.auto_advance:
            input("\nPress ENTER to execute this scenario...")
        else:
            print("\nExecuting scenario...")
            time.sleep(2)
        
        print()
    
    def run_scenario(self, scenario: DemoScenario) -> bool:
        """Run a single demo scenario.
        
        Args:
            scenario: The scenario to run
        
        Returns:
            True if scenario executed successfully
        """
        try:
            # Reset stream handler
            self.stream_handler.reset()
            
            # Prepare context
            context = {
                "output_dir": self.config.output_dir,
                "data_path": self.config.data_path
            }
            
            # Execute query
            start_time = time.time()
            response = self.orchestrator.process(scenario.query, context)
            execution_time = time.time() - start_time
            
            # Display results
            print("\n" + "=" * 80)
            print("  RESPONSE")
            print("=" * 80 + "\n")
            print(response.synthesized_response)
            print("\n" + "-" * 80)
            print(f"Execution Time: {execution_time:.2f}s")
            print(f"Actual Routing: {' → '.join(response.routing)}")
            print(f"Specialists Invoked: {len(response.specialist_responses)}")
            
            if response.charts:
                print(f"Charts Generated: {len(response.charts)}")
            
            print("-" * 80)
            
            return True
            
        except Exception as e:
            logger.error(f"Scenario execution failed: {e}", exc_info=True)
            print(f"\n✗ Error executing scenario: {e}")
            return False
    
    def pause_between_scenarios(self, duration: float) -> None:
        """Pause between scenarios for presenter explanation.
        
        Args:
            duration: Pause duration in seconds
        """
        if not self.auto_advance:
            input(f"\nPress ENTER to continue to next scenario...")
        else:
            print(f"\nPausing for {duration} seconds...")
            time.sleep(duration)
    
    def run(self) -> int:
        """Run the complete demo walkthrough.
        
        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            # Display welcome
            self.display_welcome()
            
            if not self.auto_advance:
                input("Press ENTER to start the demo...")
            else:
                time.sleep(3)
            
            # Run each scenario
            for i, scenario in enumerate(self.scenarios, 1):
                # Display scenario header
                self.display_scenario_header(scenario, i)
                
                # Run scenario
                success = self.run_scenario(scenario)
                
                if not success:
                    print(f"\n✗ Scenario {i} failed. Continuing to next scenario...")
                
                # Pause between scenarios (except after last one)
                if i < len(self.scenarios):
                    self.pause_between_scenarios(scenario.pause_duration)
            
            # Display completion message
            print("\n" + "=" * 80)
            print("  DEMO COMPLETE")
            print("=" * 80)
            print(f"\nCompleted {len(self.scenarios)} scenarios successfully!")
            print("\nKey Takeaways:")
            print("  ✓ Star topology enables flexible specialist coordination")
            print("  ✓ Orchestrator intelligently routes queries to appropriate experts")
            print("  ✓ Investigation stream provides full transparency")
            print("  ✓ Multi-domain queries leverage multiple specialists seamlessly")
            print("  ✓ Response synthesis creates coherent, comprehensive answers")
            print("\nThank you for watching the DS-Star demo!")
            print("=" * 80 + "\n")
            
            return 0
            
        except KeyboardInterrupt:
            print("\n\nDemo interrupted by user. Exiting...")
            return 0
        
        except Exception as e:
            logger.error(f"Demo failed: {e}", exc_info=True)
            print(f"\n✗ Demo failed: {e}")
            return 1


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="DS-Star Multi-Agent System - Automated Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run interactive demo (pause between scenarios)
  python demo/run_demo.py
  
  # Run automated demo (auto-advance)
  python demo/run_demo.py --auto
  
  # Run in verbose mode to see detailed investigation stream
  python demo/run_demo.py --verbose
  
  # Use a different model
  python demo/run_demo.py --model us.amazon.nova-pro-v1:0
        """
    )
    
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-advance between scenarios (no manual pauses)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose investigation stream output"
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
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    return parser.parse_args()


def main() -> int:
    """Main entry point for demo script.
    
    Returns:
        Exit code
    """
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Load configuration
        if args.config:
            config = Config.load(config_file=args.config)
        else:
            config = Config.load()
        
        # Override with CLI arguments
        if args.model:
            config.model_id = args.model
        if args.region:
            config.region = args.region
        if args.verbose:
            config.verbose = True
        
        # Create demo instance
        demo = DSStarDemo(config, auto_advance=args.auto)
        
        # Initialize system
        if not demo.initialize():
            print("\n✗ Failed to initialize demo system.")
            return 1
        
        # Run demo
        return demo.run()
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Exiting...")
        return 0
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n✗ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
