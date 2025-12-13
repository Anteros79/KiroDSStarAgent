"""Airline operations data loader and query tool."""

import logging
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class AirlineDataLoader:
    """Loads and provides access to airline operations dataset.
    
    This class handles loading the sample airline operations data,
    validating the schema, and providing convenient access methods
    for data exploration and analysis.
    """
    
    # Expected schema for airline operations dataset
    REQUIRED_COLUMNS = {
        "flight_id": "object",
        "airline": "object",
        "origin": "object",
        "destination": "object",
        "scheduled_departure": "object",
        "actual_departure": "object",
        "delay_minutes": "int64",
        "delay_cause": "object",
        "load_factor": "float64",
        "turnaround_minutes": "int64",
        "cancelled": "bool",
        "date": "object",
    }
    
    def __init__(self, data_path: str):
        """Initialize the data loader.
        
        Args:
            data_path: Path to the airline operations CSV file
        """
        self.data_path = Path(data_path)
        self._df: Optional[pd.DataFrame] = None
    
    def load(self) -> pd.DataFrame:
        """Load the airline operations dataset from CSV.
        
        Returns:
            DataFrame containing the airline operations data
        
        Raises:
            FileNotFoundError: If the data file doesn't exist
            ValueError: If the data file has invalid schema
        """
        if not self.data_path.exists():
            raise FileNotFoundError(
                f"Airline operations data file not found: {self.data_path}"
            )
        
        logger.info(f"Loading airline operations data from {self.data_path}")
        
        # Load CSV
        self._df = pd.read_csv(self.data_path)
        
        # Validate schema
        self._validate_schema()
        
        logger.info(f"Loaded {len(self._df)} flight records")
        
        return self._df
    
    def _validate_schema(self) -> None:
        """Validate that the loaded DataFrame has the expected schema.
        
        Raises:
            ValueError: If required columns are missing or have wrong types
        """
        if self._df is None:
            raise ValueError("No data loaded. Call load() first.")
        
        # Check for missing columns
        missing_columns = set(self.REQUIRED_COLUMNS.keys()) - set(self._df.columns)
        if missing_columns:
            raise ValueError(
                f"Missing required columns in dataset: {missing_columns}"
            )
        
        # Check data types for each column
        for col, expected_dtype in self.REQUIRED_COLUMNS.items():
            actual_dtype = str(self._df[col].dtype)
            
            # Allow some flexibility in dtype matching
            # (e.g., int64 vs int32, object for strings)
            if expected_dtype == "object" and actual_dtype != "object":
                # Try to convert to string/object type
                logger.warning(
                    f"Column '{col}' has dtype '{actual_dtype}', expected '{expected_dtype}'. "
                    f"Attempting conversion."
                )
                self._df[col] = self._df[col].astype("object")
            elif expected_dtype.startswith("int") and not actual_dtype.startswith("int"):
                raise ValueError(
                    f"Column '{col}' has dtype '{actual_dtype}', expected integer type"
                )
            elif expected_dtype.startswith("float") and not actual_dtype.startswith("float"):
                raise ValueError(
                    f"Column '{col}' has dtype '{actual_dtype}', expected float type"
                )
            elif expected_dtype == "bool" and actual_dtype != "bool":
                raise ValueError(
                    f"Column '{col}' has dtype '{actual_dtype}', expected bool"
                )
        
        logger.info("Schema validation passed")
    
    def get_schema(self) -> Dict[str, str]:
        """Get the schema of the airline operations dataset.
        
        Returns:
            Dictionary mapping column names to data types
        
        Raises:
            ValueError: If no data has been loaded
        """
        if self._df is None:
            raise ValueError("No data loaded. Call load() first.")
        
        return {col: str(dtype) for col, dtype in self._df.dtypes.items()}
    
    def get_sample(self, n: int = 5) -> pd.DataFrame:
        """Get a sample of the airline operations data.
        
        Args:
            n: Number of rows to return (default: 5)
        
        Returns:
            DataFrame with n sample rows
        
        Raises:
            ValueError: If no data has been loaded
        """
        if self._df is None:
            raise ValueError("No data loaded. Call load() first.")
        
        return self._df.head(n)
    
    @property
    def data(self) -> pd.DataFrame:
        """Get the loaded DataFrame.
        
        Returns:
            The loaded airline operations DataFrame
        
        Raises:
            ValueError: If no data has been loaded
        """
        if self._df is None:
            raise ValueError("No data loaded. Call load() first.")
        
        return self._df
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics for the dataset.
        
        Returns:
            Dictionary containing summary statistics
        
        Raises:
            ValueError: If no data has been loaded
        """
        if self._df is None:
            raise ValueError("No data loaded. Call load() first.")
        
        total_flights = len(self._df)
        cancelled_flights = self._df["cancelled"].sum()
        delayed_flights = (
            (self._df["delay_minutes"] >= 15) & (~self._df["cancelled"])
        ).sum()
        
        return {
            "total_flights": total_flights,
            "cancelled_flights": int(cancelled_flights),
            "cancelled_rate": float(cancelled_flights / total_flights),
            "delayed_flights": int(delayed_flights),
            "delayed_rate": float(delayed_flights / total_flights),
            "airlines": sorted(self._df["airline"].unique().tolist()),
            "airports": sorted(
                set(self._df["origin"].unique()) | set(self._df["destination"].unique())
            ),
            "date_range": {
                "start": self._df["date"].min(),
                "end": self._df["date"].max(),
            },
            "avg_delay_minutes": float(
                self._df[~self._df["cancelled"]]["delay_minutes"].mean()
            ),
            "avg_load_factor": float(
                self._df[~self._df["cancelled"]]["load_factor"].mean()
            ),
        }



# Global data loader instance for the tool
_global_loader: Optional[AirlineDataLoader] = None


def initialize_data_loader(data_path: str) -> None:
    """Initialize the global data loader instance.
    
    This should be called once at application startup to load the
    airline operations dataset for use by the query_airline_data tool.
    
    Args:
        data_path: Path to the airline operations CSV file
    """
    global _global_loader
    _global_loader = AirlineDataLoader(data_path)
    _global_loader.load()
    logger.info("Global airline data loader initialized")


def get_data_loader() -> AirlineDataLoader:
    """Get the global data loader instance.
    
    Returns:
        The initialized AirlineDataLoader instance
    
    Raises:
        RuntimeError: If the data loader hasn't been initialized
    """
    if _global_loader is None:
        raise RuntimeError(
            "Data loader not initialized. Call initialize_data_loader() first."
        )
    return _global_loader


# Import tool decorator from strands
try:
    from strands import tool
except ImportError:
    # Fallback for testing without strands installed
    def tool(func):
        """Fallback tool decorator for testing."""
        return func


@tool
def query_airline_data(query: str) -> str:
    """Execute pandas operations on airline operations dataset.
    
    This tool provides access to a comprehensive airline operations dataset
    containing flight records with various KPIs and operational metrics.
    
    Available columns:
    - flight_id: Unique flight identifier (e.g., "AA1234")
    - airline: Two-letter airline code (AA, UA, DL, SW, JB)
    - origin: Origin airport code (e.g., "JFK", "LAX")
    - destination: Destination airport code
    - scheduled_departure: ISO format datetime of scheduled departure
    - actual_departure: ISO format datetime of actual departure (empty if cancelled)
    - delay_minutes: Minutes of delay (0-180+)
    - delay_cause: Cause of delay if delayed (weather, mechanical, crew, traffic, security)
    - load_factor: Passenger capacity utilization (0.0 to 1.0)
    - turnaround_minutes: Time between arrival and next departure (25-120)
    - cancelled: Boolean indicating if flight was cancelled
    - date: ISO format date of the flight
    
    Example queries:
    - "What is the average delay for each airline?"
    - "Show me the top 5 routes with highest cancellation rates"
    - "Calculate on-time performance (flights with <15 min delay) by airline"
    - "What are the most common delay causes?"
    - "Show load factor distribution across airlines"
    
    Args:
        query: Natural language description of the data analysis to perform
    
    Returns:
        String containing the analysis results, formatted for readability
    """
    try:
        loader = get_data_loader()
        df = loader.data
        
        # Parse the query and execute appropriate pandas operations
        # This is a simplified implementation - in production, you might use
        # an LLM to generate pandas code or a more sophisticated query parser
        
        query_lower = query.lower()
        
        # Handle common query patterns
        if "average delay" in query_lower and "airline" in query_lower:
            result = df[~df["cancelled"]].groupby("airline")["delay_minutes"].mean()
            return f"Average delay by airline:\n{result.to_string()}"
        
        elif "cancellation rate" in query_lower or "cancelled" in query_lower:
            if "route" in query_lower:
                df["route"] = df["origin"] + "-" + df["destination"]
                route_stats = df.groupby("route").agg({
                    "cancelled": ["sum", "count"]
                })
                route_stats.columns = ["cancelled", "total"]
                route_stats["cancellation_rate"] = (
                    route_stats["cancelled"] / route_stats["total"]
                )
                result = route_stats.sort_values("cancellation_rate", ascending=False).head(5)
                return f"Top 5 routes by cancellation rate:\n{result.to_string()}"
            else:
                result = df.groupby("airline")["cancelled"].agg(["sum", "count"])
                result["rate"] = result["sum"] / result["count"]
                return f"Cancellation rates by airline:\n{result.to_string()}"
        
        elif "on-time performance" in query_lower or "otp" in query_lower:
            df_active = df[~df["cancelled"]].copy()
            df_active["on_time"] = df_active["delay_minutes"] < 15
            result = df_active.groupby("airline")["on_time"].agg(["sum", "count"])
            result["otp_rate"] = result["sum"] / result["count"]
            return f"On-Time Performance (OTP) by airline:\n{result.to_string()}"
        
        elif "delay cause" in query_lower:
            delay_causes = df[df["delay_minutes"] >= 15]["delay_cause"].value_counts()
            return f"Delay causes (for flights delayed 15+ minutes):\n{delay_causes.to_string()}"
        
        elif "load factor" in query_lower:
            result = df[~df["cancelled"]].groupby("airline")["load_factor"].agg(["mean", "min", "max"])
            return f"Load factor statistics by airline:\n{result.to_string()}"
        
        elif "summary" in query_lower or "overview" in query_lower:
            stats = loader.get_summary_stats()
            return (
                f"Dataset Summary:\n"
                f"  Total flights: {stats['total_flights']}\n"
                f"  Cancelled: {stats['cancelled_flights']} ({stats['cancelled_rate']:.1%})\n"
                f"  Delayed (15+ min): {stats['delayed_flights']} ({stats['delayed_rate']:.1%})\n"
                f"  Airlines: {', '.join(stats['airlines'])}\n"
                f"  Airports: {len(stats['airports'])} airports\n"
                f"  Date range: {stats['date_range']['start']} to {stats['date_range']['end']}\n"
                f"  Avg delay: {stats['avg_delay_minutes']:.1f} minutes\n"
                f"  Avg load factor: {stats['avg_load_factor']:.1%}"
            )
        
        else:
            # For unrecognized queries, provide a helpful message
            return (
                f"I received the query: '{query}'\n\n"
                f"I can help with queries about:\n"
                f"- Average delays by airline\n"
                f"- Cancellation rates by airline or route\n"
                f"- On-time performance (OTP) by airline\n"
                f"- Delay causes analysis\n"
                f"- Load factor statistics\n"
                f"- Dataset summary/overview\n\n"
                f"Please rephrase your query to match one of these patterns, "
                f"or ask for a 'summary' to see overall statistics."
            )
    
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return f"Error processing query: {str(e)}"
