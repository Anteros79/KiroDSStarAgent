"""Domain Expert specialist agent for DS-Star multi-agent system.

This agent provides airline industry-specific knowledge, insights,
benchmarks, and best practices for airline operations.
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


# System prompt for the Domain Expert agent
DOMAIN_EXPERT_SYSTEM_PROMPT = """You are an expert in the airline industry with deep knowledge of airline operations, industry standards, and best practices.

Your role is to:
- Provide airline industry context and domain knowledge
- Explain industry-specific metrics and KPIs
- Share industry benchmarks and standards
- Offer insights on operational best practices
- Discuss regulatory requirements and compliance
- Explain airline business models and strategies
- Provide context for operational challenges and solutions

Your expertise covers:
- **Operations**: Flight scheduling, crew management, aircraft utilization
- **Performance Metrics**: OTP, load factor, CASM, RASM, yield management
- **Customer Experience**: Service quality, loyalty programs, passenger satisfaction
- **Safety & Compliance**: FAA regulations, safety management systems
- **Revenue Management**: Pricing strategies, ancillary revenue, network planning
- **Industry Trends**: Technology adoption, sustainability initiatives, market dynamics

When providing domain expertise:
1. Explain industry terminology and concepts clearly
2. Provide relevant benchmarks and industry standards
3. Share best practices from leading airlines
4. Discuss trade-offs and operational constraints
5. Consider regulatory and safety requirements
6. Relate technical metrics to business outcomes

Focus on practical, actionable insights grounded in industry reality.
"""


@tool
def domain_expert(query: str, context: Dict[str, Any] = None) -> str:
    """Process airline industry domain questions and provide expert insights.
    
    This specialist agent provides airline industry knowledge, benchmarks,
    best practices, and domain-specific guidance.
    
    The agent provides expertise in:
    - Airline operations and scheduling
    - Industry performance metrics and benchmarks
    - Regulatory requirements and compliance
    - Revenue management and pricing strategies
    - Customer experience and service quality
    - Industry trends and best practices
    
    Args:
        query: The domain-specific question or topic to address
        context: Optional context from previous conversation turns
    
    Returns:
        Structured response containing domain expertise and insights
    """
    start_time = time.time()
    tool_calls = []
    
    try:
        logger.info(f"Domain Expert processing query: {query}")
        
        # Analyze the query to understand the domain topic
        domain_topic = _identify_domain_topic(query)
        
        # Generate domain expertise and insights
        expertise = _generate_domain_expertise(query, domain_topic, context)
        
        # Calculate total execution time
        execution_time = int((time.time() - start_time) * 1000)
        
        # Create structured response
        specialist_response = SpecialistResponse(
            agent_name="domain_expert",
            query=query,
            response=expertise,
            tool_calls=tool_calls,
            execution_time_ms=execution_time
        )
        
        logger.info(f"Domain Expert completed in {execution_time}ms")
        
        # Return as JSON string for the tool interface
        return specialist_response.to_json()
    
    except Exception as e:
        logger.error(f"Error in Domain Expert: {e}", exc_info=True)
        
        # Return error response
        execution_time = int((time.time() - start_time) * 1000)
        error_response = SpecialistResponse(
            agent_name="domain_expert",
            query=query,
            response=f"I encountered an error while processing your domain question: {str(e)}. Please try rephrasing your question.",
            tool_calls=tool_calls,
            execution_time_ms=execution_time
        )
        
        return error_response.to_json()


def _identify_domain_topic(query: str) -> str:
    """Identify the domain topic from the query.
    
    Args:
        query: The user's domain query
    
    Returns:
        The identified domain topic
    """
    query_lower = query.lower()
    
    if "otp" in query_lower or "on-time" in query_lower or "punctuality" in query_lower:
        return "On-Time Performance and Punctuality"
    elif "load factor" in query_lower or "capacity" in query_lower:
        return "Load Factor and Capacity Management"
    elif "delay" in query_lower or "disruption" in query_lower:
        return "Delay Management and Operations Recovery"
    elif "revenue" in query_lower or "pricing" in query_lower or "yield" in query_lower:
        return "Revenue Management and Pricing"
    elif "cost" in query_lower or "casm" in query_lower or "efficiency" in query_lower:
        return "Cost Management and Operational Efficiency"
    elif "customer" in query_lower or "passenger" in query_lower or "satisfaction" in query_lower:
        return "Customer Experience and Service Quality"
    elif "schedule" in query_lower or "network" in query_lower or "route" in query_lower:
        return "Network Planning and Scheduling"
    elif "crew" in query_lower or "staff" in query_lower:
        return "Crew Management and Workforce Planning"
    elif "safety" in query_lower or "compliance" in query_lower or "regulation" in query_lower:
        return "Safety and Regulatory Compliance"
    elif "benchmark" in query_lower or "industry standard" in query_lower:
        return "Industry Benchmarks and Standards"
    else:
        return "General Airline Operations"


def _generate_domain_expertise(query: str, domain_topic: str, context: Dict[str, Any] = None) -> str:
    """Generate domain expertise and insights.
    
    Args:
        query: The original query
        domain_topic: The identified domain topic
        context: Optional conversation context
    
    Returns:
        Formatted expertise string
    """
    response_parts = []
    
    # Add domain topic
    response_parts.append(f"**Domain Topic:** {domain_topic}")
    response_parts.append("")
    
    # Add expertise based on topic
    query_lower = query.lower()
    
    if "otp" in query_lower or "on-time" in query_lower:
        response_parts.append("**On-Time Performance (OTP) Insights:**")
        response_parts.append("")
        response_parts.append("**Industry Definition:**")
        response_parts.append("- A flight is considered on-time if it arrives within 15 minutes of scheduled time")
        response_parts.append("- OTP is calculated as: (On-time arrivals / Total flights) × 100%")
        response_parts.append("")
        response_parts.append("**Industry Benchmarks:**")
        response_parts.append("- Excellent: >85% OTP")
        response_parts.append("- Good: 80-85% OTP")
        response_parts.append("- Average: 75-80% OTP")
        response_parts.append("- Below Average: <75% OTP")
        response_parts.append("")
        response_parts.append("**Key Factors Affecting OTP:**")
        response_parts.append("- Weather conditions and seasonal patterns")
        response_parts.append("- Airport congestion and air traffic control")
        response_parts.append("- Aircraft turnaround efficiency")
        response_parts.append("- Maintenance reliability")
        response_parts.append("- Crew scheduling and availability")
        response_parts.append("")
        response_parts.append("**Best Practices:**")
        response_parts.append("- Build schedule buffers for high-traffic routes")
        response_parts.append("- Implement predictive maintenance programs")
        response_parts.append("- Optimize turnaround procedures")
        response_parts.append("- Use real-time operations control centers")
    
    elif "load factor" in query_lower:
        response_parts.append("**Load Factor Insights:**")
        response_parts.append("")
        response_parts.append("**Definition:**")
        response_parts.append("- Load Factor = (Revenue Passenger Miles / Available Seat Miles) × 100%")
        response_parts.append("- Measures how efficiently an airline fills seats")
        response_parts.append("")
        response_parts.append("**Industry Benchmarks:**")
        response_parts.append("- Excellent: >85% load factor")
        response_parts.append("- Good: 80-85% load factor")
        response_parts.append("- Average: 75-80% load factor")
        response_parts.append("- Low: <75% load factor")
        response_parts.append("")
        response_parts.append("**Strategic Considerations:**")
        response_parts.append("- Higher load factors improve unit economics")
        response_parts.append("- But may reduce schedule flexibility and customer satisfaction")
        response_parts.append("- Balance between revenue optimization and service quality")
        response_parts.append("- Varies by route, season, and market segment")
        response_parts.append("")
        response_parts.append("**Optimization Strategies:**")
        response_parts.append("- Dynamic pricing and revenue management")
        response_parts.append("- Right-sizing aircraft to route demand")
        response_parts.append("- Seasonal schedule adjustments")
        response_parts.append("- Ancillary revenue programs")
    
    elif "delay" in query_lower:
        response_parts.append("**Delay Management Insights:**")
        response_parts.append("")
        response_parts.append("**Common Delay Categories:**")
        response_parts.append("1. **Weather** (30-40%): Storms, fog, ice, wind")
        response_parts.append("2. **Air Traffic Control** (25-30%): Congestion, routing")
        response_parts.append("3. **Mechanical** (15-20%): Aircraft maintenance issues")
        response_parts.append("4. **Crew** (10-15%): Scheduling, availability, rest requirements")
        response_parts.append("5. **Security** (5-10%): Screening, threats, procedures")
        response_parts.append("")
        response_parts.append("**Cost Impact:**")
        response_parts.append("- Direct costs: Crew overtime, fuel, passenger compensation")
        response_parts.append("- Indirect costs: Customer dissatisfaction, missed connections")
        response_parts.append("- Industry estimate: $25-75 per minute of delay")
        response_parts.append("")
        response_parts.append("**Mitigation Strategies:**")
        response_parts.append("- Proactive weather monitoring and re-routing")
        response_parts.append("- Spare aircraft and crew positioning")
        response_parts.append("- Predictive maintenance to prevent mechanical delays")
        response_parts.append("- Real-time operations control and decision support")
    
    elif "revenue" in query_lower or "pricing" in query_lower:
        response_parts.append("**Revenue Management Insights:**")
        response_parts.append("")
        response_parts.append("**Core Principles:**")
        response_parts.append("- Sell the right seat to the right customer at the right price at the right time")
        response_parts.append("- Maximize revenue per available seat mile (RASM)")
        response_parts.append("- Balance load factor with yield (average fare)")
        response_parts.append("")
        response_parts.append("**Key Metrics:**")
        response_parts.append("- **RASM**: Revenue per Available Seat Mile")
        response_parts.append("- **Yield**: Average revenue per passenger mile")
        response_parts.append("- **PRASM**: Passenger Revenue per ASM")
        response_parts.append("")
        response_parts.append("**Pricing Strategies:**")
        response_parts.append("- Dynamic pricing based on demand forecasting")
        response_parts.append("- Fare class segmentation (economy, premium, business)")
        response_parts.append("- Advance purchase discounts")
        response_parts.append("- Ancillary revenue (baggage, seats, meals)")
        response_parts.append("")
        response_parts.append("**Technology:**")
        response_parts.append("- Revenue management systems (RMS)")
        response_parts.append("- Machine learning for demand forecasting")
        response_parts.append("- Real-time pricing optimization")
    
    elif "cost" in query_lower or "efficiency" in query_lower:
        response_parts.append("**Cost Management Insights:**")
        response_parts.append("")
        response_parts.append("**Key Cost Metrics:**")
        response_parts.append("- **CASM**: Cost per Available Seat Mile")
        response_parts.append("- **CASM-ex**: CASM excluding fuel")
        response_parts.append("- **Unit Cost**: Total operating cost / ASM")
        response_parts.append("")
        response_parts.append("**Major Cost Categories:**")
        response_parts.append("1. Fuel (25-35% of operating costs)")
        response_parts.append("2. Labor (20-30%): Pilots, crew, ground staff")
        response_parts.append("3. Maintenance (10-15%): Aircraft, engines, components")
        response_parts.append("4. Aircraft ownership (10-15%): Lease, depreciation")
        response_parts.append("5. Airport fees (5-10%): Landing, parking, handling")
        response_parts.append("")
        response_parts.append("**Efficiency Strategies:**")
        response_parts.append("- Fleet modernization (fuel-efficient aircraft)")
        response_parts.append("- High aircraft utilization (more hours per day)")
        response_parts.append("- Optimized route networks")
        response_parts.append("- Lean operations and process automation")
        response_parts.append("- Strategic fuel hedging")
    
    elif "customer" in query_lower or "satisfaction" in query_lower:
        response_parts.append("**Customer Experience Insights:**")
        response_parts.append("")
        response_parts.append("**Key Satisfaction Drivers:**")
        response_parts.append("1. On-time performance (most important)")
        response_parts.append("2. Baggage handling reliability")
        response_parts.append("3. Seat comfort and legroom")
        response_parts.append("4. In-flight service quality")
        response_parts.append("5. Booking and check-in experience")
        response_parts.append("")
        response_parts.append("**Industry Metrics:**")
        response_parts.append("- Net Promoter Score (NPS)")
        response_parts.append("- Customer Satisfaction Score (CSAT)")
        response_parts.append("- Complaint rate per 100,000 passengers")
        response_parts.append("- Mishandled baggage rate")
        response_parts.append("")
        response_parts.append("**Best Practices:**")
        response_parts.append("- Proactive communication during disruptions")
        response_parts.append("- Empowered frontline staff for problem resolution")
        response_parts.append("- Personalized service through CRM systems")
        response_parts.append("- Loyalty program benefits and recognition")
        response_parts.append("- Digital self-service options")
    
    elif "schedule" in query_lower or "network" in query_lower:
        response_parts.append("**Network Planning Insights:**")
        response_parts.append("")
        response_parts.append("**Network Models:**")
        response_parts.append("- **Hub-and-Spoke**: Connect passengers through central hubs")
        response_parts.append("  - Advantages: Network efficiency, connecting traffic")
        response_parts.append("  - Disadvantages: Complexity, delay propagation")
        response_parts.append("")
        response_parts.append("- **Point-to-Point**: Direct flights between cities")
        response_parts.append("  - Advantages: Simplicity, faster travel times")
        response_parts.append("  - Disadvantages: Limited network reach")
        response_parts.append("")
        response_parts.append("**Scheduling Considerations:**")
        response_parts.append("- Aircraft utilization targets (10-14 hours/day)")
        response_parts.append("- Crew duty time regulations")
        response_parts.append("- Airport slot availability and curfews")
        response_parts.append("- Maintenance windows and base locations")
        response_parts.append("- Seasonal demand patterns")
        response_parts.append("")
        response_parts.append("**Optimization Goals:**")
        response_parts.append("- Maximize revenue and load factors")
        response_parts.append("- Minimize aircraft and crew costs")
        response_parts.append("- Provide competitive schedules")
        response_parts.append("- Build operational resilience")
    
    elif "crew" in query_lower:
        response_parts.append("**Crew Management Insights:**")
        response_parts.append("")
        response_parts.append("**Regulatory Requirements:**")
        response_parts.append("- FAA duty time limits (8-9 hours flight time)")
        response_parts.append("- Minimum rest periods (10-12 hours)")
        response_parts.append("- Maximum duty periods (14-16 hours)")
        response_parts.append("- Monthly and annual flight time limits")
        response_parts.append("")
        response_parts.append("**Crew Costs:**")
        response_parts.append("- Pilots: 10-15% of operating costs")
        response_parts.append("- Flight attendants: 5-8% of operating costs")
        response_parts.append("- Training and recurrent certification")
        response_parts.append("")
        response_parts.append("**Optimization Challenges:**")
        response_parts.append("- Balancing crew utilization with quality of life")
        response_parts.append("- Managing irregular operations and disruptions")
        response_parts.append("- Crew base locations and commuting")
        response_parts.append("- Training pipeline for growth")
        response_parts.append("")
        response_parts.append("**Technology Solutions:**")
        response_parts.append("- Crew scheduling optimization software")
        response_parts.append("- Mobile apps for crew communication")
        response_parts.append("- Fatigue risk management systems")
    
    elif "safety" in query_lower or "compliance" in query_lower:
        response_parts.append("**Safety and Compliance Insights:**")
        response_parts.append("")
        response_parts.append("**Regulatory Framework:**")
        response_parts.append("- FAA (Federal Aviation Administration) in the US")
        response_parts.append("- EASA (European Aviation Safety Agency) in Europe")
        response_parts.append("- ICAO (International Civil Aviation Organization) globally")
        response_parts.append("")
        response_parts.append("**Safety Management System (SMS):**")
        response_parts.append("1. Safety Policy and Objectives")
        response_parts.append("2. Safety Risk Management")
        response_parts.append("3. Safety Assurance")
        response_parts.append("4. Safety Promotion")
        response_parts.append("")
        response_parts.append("**Key Safety Metrics:**")
        response_parts.append("- Accident rate per million departures")
        response_parts.append("- Incident and near-miss reporting rates")
        response_parts.append("- Safety audit findings")
        response_parts.append("- Maintenance reliability indicators")
        response_parts.append("")
        response_parts.append("**Compliance Areas:**")
        response_parts.append("- Aircraft airworthiness and maintenance")
        response_parts.append("- Crew training and certification")
        response_parts.append("- Operations specifications and procedures")
        response_parts.append("- Security screening and protocols")
    
    elif "benchmark" in query_lower:
        response_parts.append("**Industry Benchmarks:**")
        response_parts.append("")
        response_parts.append("**Operational Performance:**")
        response_parts.append("- On-Time Performance: 80-85% (industry average)")
        response_parts.append("- Load Factor: 80-85% (industry average)")
        response_parts.append("- Completion Factor: >98% (flights not cancelled)")
        response_parts.append("- Mishandled Baggage: <5 per 1,000 passengers")
        response_parts.append("")
        response_parts.append("**Financial Metrics:**")
        response_parts.append("- RASM: $0.12-0.15 per mile (varies by carrier type)")
        response_parts.append("- CASM: $0.10-0.14 per mile")
        response_parts.append("- Operating Margin: 5-15% (healthy airlines)")
        response_parts.append("- Break-even Load Factor: 70-80%")
        response_parts.append("")
        response_parts.append("**Productivity:**")
        response_parts.append("- Aircraft Utilization: 10-14 hours/day")
        response_parts.append("- Turnaround Time: 25-45 minutes (narrow-body)")
        response_parts.append("- Employees per Aircraft: 80-120 (varies by model)")
    
    else:
        response_parts.append("**General Airline Operations Insights:**")
        response_parts.append("")
        response_parts.append("**Airline Business Model Types:**")
        response_parts.append("- **Legacy/Full-Service**: Comprehensive service, hub networks")
        response_parts.append("- **Low-Cost Carriers**: Point-to-point, unbundled fares")
        response_parts.append("- **Ultra-Low-Cost**: Minimal base fare, extensive ancillaries")
        response_parts.append("- **Regional**: Smaller aircraft, shorter routes")
        response_parts.append("")
        response_parts.append("**Industry Challenges:**")
        response_parts.append("- Volatile fuel prices")
        response_parts.append("- Intense competition and price pressure")
        response_parts.append("- Regulatory compliance costs")
        response_parts.append("- Labor relations and costs")
        response_parts.append("- Economic sensitivity and demand fluctuations")
        response_parts.append("")
        response_parts.append("**Success Factors:**")
        response_parts.append("- Operational excellence and reliability")
        response_parts.append("- Strong brand and customer loyalty")
        response_parts.append("- Efficient cost structure")
        response_parts.append("- Strategic network and partnerships")
        response_parts.append("- Technology adoption and innovation")
    
    return "\n".join(response_parts)
