"""Statistics Expert specialist agent for DS-Star multi-agent system.

This agent handles hypothesis testing, statistical analysis,
probability distributions, and advanced statistical methods.
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


# System prompt for the Statistics Expert agent
STATISTICS_EXPERT_SYSTEM_PROMPT = """You are an expert Statistician specializing in hypothesis testing and advanced statistical analysis.

Your role is to:
- Design and recommend appropriate statistical tests for research questions
- Explain statistical concepts in clear, accessible language
- Perform hypothesis testing and interpret p-values
- Analyze probability distributions and statistical significance
- Provide guidance on experimental design and sample size calculations
- Recommend appropriate statistical methods for different data types
- Interpret confidence intervals and effect sizes

When working with statistical questions:
1. Clarify the research question and hypotheses
2. Recommend appropriate statistical tests (t-tests, ANOVA, chi-square, etc.)
3. Explain assumptions and prerequisites for each test
4. Interpret results in the context of the business problem
5. Discuss statistical significance vs. practical significance
6. Provide recommendations based on statistical findings

Focus on rigorous statistical methodology while making concepts accessible to non-statisticians.
"""


@tool
def statistics_expert(query: str, context: Dict[str, Any] = None) -> str:
    """Process statistical analysis queries and hypothesis testing questions.
    
    This specialist agent handles hypothesis testing, statistical test selection,
    probability analysis, and advanced statistical methods.
    
    The agent provides expertise in:
    - Hypothesis testing (t-tests, ANOVA, chi-square, etc.)
    - Statistical significance and p-value interpretation
    - Confidence intervals and effect sizes
    - Experimental design and sample size calculations
    - Distribution analysis and normality testing
    - Correlation and regression analysis
    
    Args:
        query: The statistical question or task to process
        context: Optional context from previous conversation turns
    
    Returns:
        Structured response containing statistical guidance and recommendations
    """
    start_time = time.time()
    tool_calls = []
    
    try:
        logger.info(f"Statistics Expert processing query: {query}")
        
        # Analyze the query to understand the statistical need
        statistical_approach = _plan_statistical_approach(query)
        
        # Generate statistical recommendations
        recommendations = _generate_statistical_guidance(query, statistical_approach, context)
        
        # Calculate total execution time
        execution_time = int((time.time() - start_time) * 1000)
        
        # Create structured response
        specialist_response = SpecialistResponse(
            agent_name="statistics_expert",
            query=query,
            response=recommendations,
            tool_calls=tool_calls,
            execution_time_ms=execution_time
        )
        
        logger.info(f"Statistics Expert completed in {execution_time}ms")
        
        # Return as JSON string for the tool interface
        return specialist_response.to_json()
    
    except Exception as e:
        logger.error(f"Error in Statistics Expert: {e}", exc_info=True)
        
        # Return error response
        execution_time = int((time.time() - start_time) * 1000)
        error_response = SpecialistResponse(
            agent_name="statistics_expert",
            query=query,
            response=f"I encountered an error while processing your statistical query: {str(e)}. Please try rephrasing your question.",
            tool_calls=tool_calls,
            execution_time_ms=execution_time
        )
        
        return error_response.to_json()


def _plan_statistical_approach(query: str) -> str:
    """Plan the statistical approach based on the query.
    
    Args:
        query: The user's statistical query
    
    Returns:
        A brief description of the statistical approach
    """
    query_lower = query.lower()
    
    if "hypothesis" in query_lower or "test" in query_lower:
        return "Design hypothesis test and select appropriate statistical test"
    elif "significance" in query_lower or "p-value" in query_lower:
        return "Interpret statistical significance and p-values"
    elif "correlation" in query_lower or "relationship" in query_lower:
        return "Analyze correlation and relationships between variables"
    elif "distribution" in query_lower or "normal" in query_lower:
        return "Analyze probability distributions and normality"
    elif "sample size" in query_lower or "power" in query_lower:
        return "Calculate sample size and statistical power"
    elif "confidence" in query_lower or "interval" in query_lower:
        return "Calculate and interpret confidence intervals"
    elif "anova" in query_lower or "compare groups" in query_lower:
        return "Compare multiple groups using ANOVA"
    else:
        return "Provide general statistical guidance"


def _generate_statistical_guidance(query: str, statistical_approach: str, context: Dict[str, Any] = None) -> str:
    """Generate statistical guidance and recommendations.
    
    Args:
        query: The original query
        statistical_approach: The planned statistical approach
        context: Optional conversation context
    
    Returns:
        Formatted guidance string
    """
    response_parts = []
    
    # Add statistical approach
    response_parts.append(f"**Statistical Approach:** {statistical_approach}")
    response_parts.append("")
    
    # Add recommendations based on query type
    query_lower = query.lower()
    
    if "hypothesis" in query_lower or "test" in query_lower:
        response_parts.append("**Hypothesis Testing Framework:**")
        response_parts.append("")
        response_parts.append("**1. Formulate Hypotheses:**")
        response_parts.append("   - Null Hypothesis (H₀): No effect or no difference")
        response_parts.append("   - Alternative Hypothesis (H₁): There is an effect or difference")
        response_parts.append("")
        response_parts.append("**2. Select Appropriate Test:**")
        response_parts.append("   - **t-test**: Compare means of two groups")
        response_parts.append("   - **ANOVA**: Compare means of three or more groups")
        response_parts.append("   - **Chi-square**: Test relationships between categorical variables")
        response_parts.append("   - **Mann-Whitney U**: Non-parametric alternative to t-test")
        response_parts.append("")
        response_parts.append("**3. Check Assumptions:**")
        response_parts.append("   - Independence of observations")
        response_parts.append("   - Normality of data (for parametric tests)")
        response_parts.append("   - Homogeneity of variance")
        response_parts.append("")
        response_parts.append("**4. Interpret Results:**")
        response_parts.append("   - p-value < 0.05: Reject null hypothesis (statistically significant)")
        response_parts.append("   - p-value ≥ 0.05: Fail to reject null hypothesis")
        response_parts.append("   - Consider effect size and practical significance")
    
    elif "significance" in query_lower or "p-value" in query_lower:
        response_parts.append("**Understanding Statistical Significance:**")
        response_parts.append("")
        response_parts.append("**P-value Interpretation:**")
        response_parts.append("- p < 0.001: Very strong evidence against H₀")
        response_parts.append("- p < 0.01: Strong evidence against H₀")
        response_parts.append("- p < 0.05: Moderate evidence against H₀ (conventional threshold)")
        response_parts.append("- p ≥ 0.05: Insufficient evidence to reject H₀")
        response_parts.append("")
        response_parts.append("**Important Considerations:**")
        response_parts.append("- Statistical significance ≠ practical significance")
        response_parts.append("- Large samples can detect tiny, meaningless differences")
        response_parts.append("- Always report effect sizes alongside p-values")
        response_parts.append("- Consider confidence intervals for more complete picture")
        response_parts.append("- Beware of p-hacking and multiple testing issues")
    
    elif "correlation" in query_lower:
        response_parts.append("**Correlation Analysis:**")
        response_parts.append("")
        response_parts.append("**Correlation Coefficients:**")
        response_parts.append("- **Pearson's r**: Linear relationship between continuous variables")
        response_parts.append("  - Range: -1 (perfect negative) to +1 (perfect positive)")
        response_parts.append("  - Assumes: Linear relationship, normality, no outliers")
        response_parts.append("")
        response_parts.append("- **Spearman's ρ**: Monotonic relationship (non-parametric)")
        response_parts.append("  - Use when: Data is ordinal or non-normal")
        response_parts.append("")
        response_parts.append("**Interpretation Guidelines:**")
        response_parts.append("- |r| < 0.3: Weak correlation")
        response_parts.append("- 0.3 ≤ |r| < 0.7: Moderate correlation")
        response_parts.append("- |r| ≥ 0.7: Strong correlation")
        response_parts.append("")
        response_parts.append("**Remember:** Correlation does not imply causation!")
    
    elif "distribution" in query_lower or "normal" in query_lower:
        response_parts.append("**Distribution Analysis:**")
        response_parts.append("")
        response_parts.append("**Testing for Normality:**")
        response_parts.append("- **Visual Methods:**")
        response_parts.append("  - Histogram: Should show bell-shaped curve")
        response_parts.append("  - Q-Q plot: Points should fall on diagonal line")
        response_parts.append("")
        response_parts.append("- **Statistical Tests:**")
        response_parts.append("  - Shapiro-Wilk test (n < 50)")
        response_parts.append("  - Kolmogorov-Smirnov test (n ≥ 50)")
        response_parts.append("")
        response_parts.append("**Common Distributions:**")
        response_parts.append("- Normal: Continuous, symmetric, bell-shaped")
        response_parts.append("- Binomial: Discrete, fixed number of trials")
        response_parts.append("- Poisson: Count data, rare events")
        response_parts.append("- Exponential: Time between events")
    
    elif "sample size" in query_lower or "power" in query_lower:
        response_parts.append("**Sample Size and Statistical Power:**")
        response_parts.append("")
        response_parts.append("**Key Concepts:**")
        response_parts.append("- **Power (1-β)**: Probability of detecting a true effect")
        response_parts.append("  - Conventional target: 80% (0.80)")
        response_parts.append("- **Alpha (α)**: Significance level (typically 0.05)")
        response_parts.append("- **Effect Size**: Magnitude of the difference you want to detect")
        response_parts.append("")
        response_parts.append("**Sample Size Considerations:**")
        response_parts.append("- Larger samples → Higher power → Better chance of detecting effects")
        response_parts.append("- Smaller effect sizes require larger samples")
        response_parts.append("- Balance statistical power with practical constraints (cost, time)")
        response_parts.append("")
        response_parts.append("**Tools:** G*Power, R pwr package, Python statsmodels")
    
    elif "confidence" in query_lower or "interval" in query_lower:
        response_parts.append("**Confidence Intervals:**")
        response_parts.append("")
        response_parts.append("**Interpretation:**")
        response_parts.append("- 95% CI: If we repeated the study 100 times, 95 intervals would contain the true parameter")
        response_parts.append("- Wider intervals → More uncertainty")
        response_parts.append("- Narrower intervals → More precision (larger sample size)")
        response_parts.append("")
        response_parts.append("**Advantages over p-values:**")
        response_parts.append("- Shows range of plausible values")
        response_parts.append("- Indicates precision of estimate")
        response_parts.append("- Provides information about practical significance")
        response_parts.append("")
        response_parts.append("**Common Confidence Levels:**")
        response_parts.append("- 90% CI: Less conservative, wider range of applications")
        response_parts.append("- 95% CI: Standard in most research")
        response_parts.append("- 99% CI: More conservative, higher certainty")
    
    elif "anova" in query_lower:
        response_parts.append("**Analysis of Variance (ANOVA):**")
        response_parts.append("")
        response_parts.append("**When to Use:**")
        response_parts.append("- Comparing means of 3+ groups")
        response_parts.append("- One categorical independent variable")
        response_parts.append("- One continuous dependent variable")
        response_parts.append("")
        response_parts.append("**Types of ANOVA:**")
        response_parts.append("- **One-way ANOVA**: One independent variable")
        response_parts.append("- **Two-way ANOVA**: Two independent variables")
        response_parts.append("- **Repeated measures ANOVA**: Same subjects measured multiple times")
        response_parts.append("")
        response_parts.append("**Post-hoc Tests:**")
        response_parts.append("- Tukey HSD: Compare all pairs of groups")
        response_parts.append("- Bonferroni: Conservative, controls family-wise error rate")
        response_parts.append("- Scheffé: Most conservative, for complex comparisons")
    
    else:
        response_parts.append("**General Statistical Guidance:**")
        response_parts.append("")
        response_parts.append("**Statistical Analysis Workflow:**")
        response_parts.append("1. Define research question and hypotheses")
        response_parts.append("2. Choose appropriate statistical test")
        response_parts.append("3. Check assumptions (normality, independence, etc.)")
        response_parts.append("4. Perform the analysis")
        response_parts.append("5. Interpret results in context")
        response_parts.append("6. Report effect sizes and confidence intervals")
        response_parts.append("")
        response_parts.append("**Best Practices:**")
        response_parts.append("- Always visualize your data first")
        response_parts.append("- Check assumptions before running tests")
        response_parts.append("- Report both statistical and practical significance")
        response_parts.append("- Be transparent about multiple testing corrections")
        response_parts.append("- Consider consulting a statistician for complex analyses")
    
    return "\n".join(response_parts)
