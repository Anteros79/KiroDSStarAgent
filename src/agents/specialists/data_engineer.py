"""Data Engineer specialist agent for DS-Star multi-agent system.

This agent handles ETL pipeline design, data transformation queries,
data quality assessment, and data integration tasks.
"""

import logging
import time
from typing import Dict, Any

from src.models import SpecialistResponse, ToolCall

logger = logging.getLogger(__name__)

# Import tool decorator from strands
try:
    from strands import tool
except ImportError:
    # Fallback for testing without strands installed
    def tool(func):
        """Fallback tool decorator for testing."""
        return func


# System prompt for the Data Engineer agent
DATA_ENGINEER_SYSTEM_PROMPT = """You are an expert Data Engineer specializing in ETL pipelines and data transformation.

Your role is to:
- Design and recommend ETL (Extract, Transform, Load) pipelines
- Suggest data transformation strategies and best practices
- Provide guidance on data quality checks and validation
- Recommend data integration approaches for multiple sources
- Advise on data storage and schema design
- Suggest data processing frameworks and tools

When working with data engineering tasks:
1. Understand the data sources and target requirements
2. Recommend appropriate ETL tools and frameworks (e.g., Apache Airflow, dbt, Spark)
3. Design scalable and maintainable data pipelines
4. Include data quality checks and error handling
5. Consider performance optimization and cost efficiency
6. Provide code examples when helpful

Focus on practical, production-ready solutions that follow industry best practices.
"""


@tool
def data_engineer(query: str, context: Dict[str, Any] = None) -> str:
    """Process data engineering queries for ETL and data transformation tasks.
    
    This specialist agent handles ETL pipeline design, data transformation
    recommendations, data quality assessment, and data integration guidance.
    
    The agent provides expertise in:
    - ETL pipeline architecture and design
    - Data transformation strategies
    - Data quality and validation
    - Data integration patterns
    - Schema design and optimization
    
    Args:
        query: The data engineering question or task to process
        context: Optional context from previous conversation turns
    
    Returns:
        Structured response containing recommendations and guidance
    """
    start_time = time.time()
    tool_calls = []
    
    try:
        logger.info(f"Data Engineer processing query: {query}")
        
        # Analyze the query to understand the data engineering need
        engineering_plan = _plan_engineering_approach(query)
        
        # Generate recommendations based on the query
        recommendations = _generate_recommendations(query, engineering_plan, context)
        
        # Calculate total execution time
        execution_time = int((time.time() - start_time) * 1000)
        
        # Create structured response
        specialist_response = SpecialistResponse(
            agent_name="data_engineer",
            query=query,
            response=recommendations,
            tool_calls=tool_calls,
            execution_time_ms=execution_time
        )
        
        logger.info(f"Data Engineer completed in {execution_time}ms")
        
        # Return as JSON string for the tool interface
        return specialist_response.to_json()
    
    except Exception as e:
        logger.error(f"Error in Data Engineer: {e}", exc_info=True)
        
        # Return error response
        execution_time = int((time.time() - start_time) * 1000)
        error_response = SpecialistResponse(
            agent_name="data_engineer",
            query=query,
            response=f"I encountered an error while processing your data engineering query: {str(e)}. Please try rephrasing your question.",
            tool_calls=tool_calls,
            execution_time_ms=execution_time
        )
        
        return error_response.to_json()


def _plan_engineering_approach(query: str) -> str:
    """Plan the data engineering approach based on the query.
    
    Args:
        query: The user's data engineering query
    
    Returns:
        A brief description of the engineering approach
    """
    query_lower = query.lower()
    
    if "etl" in query_lower or "pipeline" in query_lower:
        return "Design ETL pipeline architecture and workflow"
    elif "transform" in query_lower or "transformation" in query_lower:
        return "Recommend data transformation strategies"
    elif "quality" in query_lower or "validation" in query_lower:
        return "Design data quality checks and validation rules"
    elif "integration" in query_lower or "integrate" in query_lower:
        return "Plan data integration approach for multiple sources"
    elif "schema" in query_lower or "database" in query_lower:
        return "Design optimal schema and data model"
    elif "performance" in query_lower or "optimize" in query_lower:
        return "Optimize data processing performance"
    else:
        return "Provide general data engineering guidance"


def _generate_recommendations(query: str, engineering_plan: str, context: Dict[str, Any] = None) -> str:
    """Generate data engineering recommendations.
    
    Args:
        query: The original query
        engineering_plan: The planned engineering approach
        context: Optional conversation context
    
    Returns:
        Formatted recommendations string
    """
    response_parts = []
    
    # Add engineering approach
    response_parts.append(f"**Engineering Approach:** {engineering_plan}")
    response_parts.append("")
    
    # Add recommendations based on query type
    query_lower = query.lower()
    
    if "etl" in query_lower or "pipeline" in query_lower:
        response_parts.append("**ETL Pipeline Recommendations:**")
        response_parts.append("- Use Apache Airflow or Prefect for orchestration and scheduling")
        response_parts.append("- Implement incremental loading to process only new/changed data")
        response_parts.append("- Add data quality checks at each pipeline stage")
        response_parts.append("- Use idempotent operations to enable safe retries")
        response_parts.append("- Log all transformations for debugging and auditing")
        response_parts.append("")
        response_parts.append("**Pipeline Stages:**")
        response_parts.append("1. Extract: Pull data from source systems")
        response_parts.append("2. Validate: Check data quality and completeness")
        response_parts.append("3. Transform: Apply business logic and transformations")
        response_parts.append("4. Load: Write to target data warehouse")
        response_parts.append("5. Monitor: Track pipeline health and data quality metrics")
    
    elif "transform" in query_lower:
        response_parts.append("**Data Transformation Best Practices:**")
        response_parts.append("- Use dbt (data build tool) for SQL-based transformations")
        response_parts.append("- Apply transformations in layers: staging → intermediate → marts")
        response_parts.append("- Document transformation logic and business rules")
        response_parts.append("- Test transformations with sample data before production")
        response_parts.append("- Version control all transformation code")
    
    elif "quality" in query_lower:
        response_parts.append("**Data Quality Framework:**")
        response_parts.append("- Completeness: Check for missing or null values")
        response_parts.append("- Accuracy: Validate data against known constraints")
        response_parts.append("- Consistency: Ensure data matches across sources")
        response_parts.append("- Timeliness: Verify data freshness and latency")
        response_parts.append("- Uniqueness: Check for duplicate records")
        response_parts.append("")
        response_parts.append("**Tools:** Great Expectations, dbt tests, custom validation scripts")
    
    elif "integration" in query_lower:
        response_parts.append("**Data Integration Strategy:**")
        response_parts.append("- Use a centralized data warehouse (Snowflake, BigQuery, Redshift)")
        response_parts.append("- Implement a medallion architecture (bronze → silver → gold)")
        response_parts.append("- Use CDC (Change Data Capture) for real-time updates")
        response_parts.append("- Standardize data formats and schemas across sources")
        response_parts.append("- Implement data lineage tracking")
    
    elif "schema" in query_lower:
        response_parts.append("**Schema Design Recommendations:**")
        response_parts.append("- Use star schema for analytical workloads")
        response_parts.append("- Denormalize for query performance")
        response_parts.append("- Add surrogate keys for dimension tables")
        response_parts.append("- Include audit columns (created_at, updated_at, created_by)")
        response_parts.append("- Use appropriate data types to optimize storage")
    
    else:
        response_parts.append("**General Data Engineering Guidance:**")
        response_parts.append("- Start with clear requirements and success criteria")
        response_parts.append("- Design for scalability and maintainability")
        response_parts.append("- Implement comprehensive monitoring and alerting")
        response_parts.append("- Document architecture decisions and data flows")
        response_parts.append("- Follow the principle of least privilege for data access")
    
    return "\n".join(response_parts)
