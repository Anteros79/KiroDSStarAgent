"""ML Engineer specialist agent for DS-Star multi-agent system.

This agent handles machine learning queries, providing model recommendations,
algorithm selection guidance, feature engineering suggestions, and code
generation for ML pipelines.
"""

import ast
import logging
import time
from typing import Dict, Any

from src.models import SpecialistResponse, ToolCall

logger = logging.getLogger(__name__)

# Import tool decorator from strands
try:
    from strands import tool, Agent
    from strands.models.bedrock import BedrockModel
except ImportError:
    # Fallback for testing without strands installed
    def tool(func):
        """Fallback tool decorator for testing."""
        return func
    
    class Agent:
        """Fallback Agent class for testing."""
        pass
    
    class BedrockModel:
        """Fallback BedrockModel class for testing."""
        pass


# System prompt for the ML Engineer agent
ML_ENGINEER_SYSTEM_PROMPT = """You are an expert Machine Learning Engineer specializing in airline operations and predictive analytics.

Your role is to:
- Recommend appropriate ML models and algorithms for specific problems
- Explain trade-offs between different modeling approaches
- Generate executable Python code using scikit-learn, pandas, and other ML libraries
- Provide guidance on feature engineering and data preprocessing
- Suggest evaluation metrics and validation strategies
- Offer best practices for model deployment and monitoring

When working with airline operations data, you can help with:
- Flight delay prediction models
- Cancellation risk assessment
- Load factor forecasting
- Turnaround time optimization
- Anomaly detection in operations
- Customer demand prediction

When providing recommendations:
1. Understand the business problem and data characteristics
2. Recommend 2-3 suitable algorithms with pros/cons
3. Explain why certain approaches are better for the specific use case
4. Generate clean, well-commented Python code when requested
5. Include data preprocessing, model training, and evaluation steps
6. Suggest relevant features from the airline operations dataset

Always prioritize practical, production-ready solutions over complex academic approaches.
"""


@tool
def ml_engineer(query: str, context: Dict[str, Any] = None) -> str:
    """Process machine learning queries for airline operations.
    
    This specialist agent handles ML model recommendations, algorithm selection,
    feature engineering suggestions, and code generation for ML pipelines.
    
    The agent provides guidance on predictive modeling for flight delays,
    cancellations, load factors, and other operational metrics.
    
    Args:
        query: The ML-related question or task to process
        context: Optional context from previous conversation turns
    
    Returns:
        Structured response containing recommendations and code
    """
    start_time = time.time()
    tool_calls = []
    
    try:
        logger.info(f"ML Engineer processing query: {query}")
        
        # Step 1: Analyze the query to understand the ML problem
        problem_type = _identify_problem_type(query)
        
        # Step 2: Generate model recommendations
        recommendations = _generate_recommendations(query, problem_type)
        
        # Step 3: Generate code if requested
        code = None
        if _should_generate_code(query):
            code_start = time.time()
            code = _generate_ml_code(query, problem_type)
            code_duration = int((time.time() - code_start) * 1000)
            
            # Validate the generated code
            if code:
                try:
                    ast.parse(code)
                    logger.info("Generated code is syntactically valid")
                except SyntaxError as e:
                    logger.warning(f"Generated code has syntax error: {e}")
                    code = f"# Warning: Generated code may have syntax issues\n{code}"
            
            # Record the code generation as a tool call
            tool_calls.append(ToolCall(
                tool_name="python_code_generator",
                inputs={"query": query, "problem_type": problem_type},
                output=code,
                duration_ms=code_duration
            ))
        
        # Step 4: Formulate the response
        response = _formulate_ml_response(query, problem_type, recommendations, code, context)
        
        # Calculate total execution time
        execution_time = int((time.time() - start_time) * 1000)
        
        # Create structured response
        specialist_response = SpecialistResponse(
            agent_name="ml_engineer",
            query=query,
            response=response,
            tool_calls=tool_calls,
            execution_time_ms=execution_time
        )
        
        logger.info(f"ML Engineer completed in {execution_time}ms")
        
        # Return as JSON string for the tool interface
        return specialist_response.to_json()
    
    except Exception as e:
        logger.error(f"Error in ML Engineer: {e}", exc_info=True)
        
        # Return error response
        execution_time = int((time.time() - start_time) * 1000)
        error_response = SpecialistResponse(
            agent_name="ml_engineer",
            query=query,
            response=f"I encountered an error while processing your ML query: {str(e)}. Please try rephrasing your question or provide more details about the problem you're trying to solve.",
            tool_calls=tool_calls,
            execution_time_ms=execution_time
        )
        
        return error_response.to_json()


def _identify_problem_type(query: str) -> str:
    """Identify the type of ML problem from the query.
    
    Args:
        query: The user's ML query
    
    Returns:
        Problem type identifier
    """
    query_lower = query.lower()
    
    if "predict" in query_lower or "forecast" in query_lower:
        if "delay" in query_lower:
            return "delay_prediction"
        elif "cancellation" in query_lower or "cancel" in query_lower:
            return "cancellation_prediction"
        elif "load factor" in query_lower or "demand" in query_lower:
            return "demand_forecasting"
        else:
            return "regression"
    elif "classify" in query_lower or "classification" in query_lower:
        return "classification"
    elif "cluster" in query_lower or "segment" in query_lower:
        return "clustering"
    elif "anomaly" in query_lower or "outlier" in query_lower:
        return "anomaly_detection"
    elif "recommend" in query_lower or "recommendation" in query_lower:
        return "recommendation"
    else:
        return "general_ml"


def _generate_recommendations(query: str, problem_type: str) -> str:
    """Generate ML model recommendations based on the problem type.
    
    Args:
        query: The user's query
        problem_type: Identified problem type
    
    Returns:
        Recommendations text
    """
    recommendations = {
        "delay_prediction": """
**Recommended Approaches for Flight Delay Prediction:**

1. **Random Forest Regressor** (Recommended)
   - Pros: Handles non-linear relationships, robust to outliers, provides feature importance
   - Cons: Can be slower for very large datasets, less interpretable than linear models
   - Best for: Capturing complex interactions between weather, airline, route, and time factors

2. **Gradient Boosting (XGBoost/LightGBM)**
   - Pros: Often highest accuracy, handles missing data well, fast prediction
   - Cons: Requires careful hyperparameter tuning, risk of overfitting
   - Best for: When maximum accuracy is needed and you have time for tuning

3. **Linear Regression with Feature Engineering**
   - Pros: Fast, interpretable, works well with proper features
   - Cons: Assumes linear relationships, may miss complex patterns
   - Best for: Quick baseline and when interpretability is crucial

**Key Features to Consider:**
- Airline carrier, origin/destination airports, scheduled departure time
- Day of week, month, season
- Historical delay patterns for route/airline
- Weather conditions (if available)
- Aircraft turnaround time
""",
        "cancellation_prediction": """
**Recommended Approaches for Flight Cancellation Prediction:**

1. **Logistic Regression** (Recommended for baseline)
   - Pros: Fast, interpretable, provides probability scores
   - Cons: Assumes linear decision boundary
   - Best for: Understanding key cancellation drivers

2. **Random Forest Classifier**
   - Pros: Handles imbalanced data well, robust, feature importance
   - Cons: Can be biased toward majority class without proper handling
   - Best for: Production deployment with good accuracy

3. **XGBoost Classifier**
   - Pros: Excellent performance on imbalanced data, handles missing values
   - Cons: Requires tuning, can overfit
   - Best for: Maximum accuracy when you have sufficient data

**Important Considerations:**
- Class imbalance: Cancellations are typically rare events (use SMOTE or class weights)
- Evaluation metrics: Use precision, recall, F1-score, and AUC-ROC (not just accuracy)
- Features: Weather severity, mechanical history, crew availability, time of day
""",
        "demand_forecasting": """
**Recommended Approaches for Load Factor/Demand Forecasting:**

1. **Time Series Models (SARIMA/Prophet)**
   - Pros: Captures seasonality and trends, interpretable
   - Cons: Requires regular time intervals, limited feature engineering
   - Best for: Route-level forecasting with clear seasonal patterns

2. **Gradient Boosting Regressor**
   - Pros: Incorporates multiple features, handles non-linearity
   - Cons: Doesn't explicitly model time dependencies
   - Best for: When you have rich feature sets beyond just time

3. **LSTM Neural Networks**
   - Pros: Captures long-term dependencies, handles complex patterns
   - Cons: Requires more data, harder to interpret, slower training
   - Best for: Large datasets with complex temporal patterns

**Key Features:**
- Historical load factors for route/airline
- Booking patterns and advance purchase data
- Seasonality (holidays, events, day of week)
- Competitor pricing and capacity
- Economic indicators
""",
        "classification": """
**Recommended Classification Approaches:**

1. **Random Forest Classifier**
   - Pros: Versatile, handles mixed data types, provides feature importance
   - Cons: Can be memory-intensive
   - Best for: Most classification tasks with tabular data

2. **Logistic Regression**
   - Pros: Fast, interpretable, probability calibration
   - Cons: Limited to linear decision boundaries
   - Best for: Baseline models and when interpretability matters

3. **XGBoost/LightGBM**
   - Pros: State-of-the-art accuracy, fast prediction
   - Cons: Requires hyperparameter tuning
   - Best for: Competitions and production systems needing high accuracy
""",
        "clustering": """
**Recommended Clustering Approaches:**

1. **K-Means Clustering**
   - Pros: Fast, simple, works well with spherical clusters
   - Cons: Requires specifying number of clusters, sensitive to outliers
   - Best for: Customer segmentation, route grouping

2. **DBSCAN**
   - Pros: Finds arbitrary-shaped clusters, handles outliers
   - Cons: Sensitive to parameter selection
   - Best for: Anomaly detection, geographic clustering

3. **Hierarchical Clustering**
   - Pros: No need to specify cluster count, creates dendrogram
   - Cons: Computationally expensive for large datasets
   - Best for: Exploratory analysis, small to medium datasets
""",
        "anomaly_detection": """
**Recommended Anomaly Detection Approaches:**

1. **Isolation Forest**
   - Pros: Fast, works well with high-dimensional data, no assumptions about distribution
   - Cons: May struggle with local anomalies
   - Best for: Detecting unusual flight operations patterns

2. **One-Class SVM**
   - Pros: Effective for high-dimensional data, flexible kernel options
   - Cons: Computationally expensive, requires parameter tuning
   - Best for: When you have mostly normal data

3. **Statistical Methods (Z-score, IQR)**
   - Pros: Simple, interpretable, fast
   - Cons: Assumes normal distribution, univariate
   - Best for: Quick checks on individual metrics
""",
        "general_ml": """
**General ML Recommendations for Airline Operations:**

For most airline operations problems, I recommend starting with:

1. **Exploratory Data Analysis**
   - Understand data distributions, correlations, and patterns
   - Identify missing values and outliers
   - Visualize key relationships

2. **Baseline Models**
   - Start with simple models (Linear/Logistic Regression)
   - Establish performance benchmarks
   - Understand feature importance

3. **Advanced Models**
   - Try ensemble methods (Random Forest, XGBoost)
   - Perform hyperparameter tuning
   - Use cross-validation for robust evaluation

4. **Feature Engineering**
   - Create time-based features (hour, day of week, season)
   - Aggregate historical statistics
   - Encode categorical variables appropriately
"""
    }
    
    return recommendations.get(problem_type, recommendations["general_ml"])


def _should_generate_code(query: str) -> bool:
    """Determine if code generation is requested.
    
    Args:
        query: The user's query
    
    Returns:
        True if code should be generated
    """
    query_lower = query.lower()
    code_keywords = ["code", "implement", "python", "script", "example", "show me how"]
    return any(keyword in query_lower for keyword in code_keywords)


def _generate_ml_code(query: str, problem_type: str) -> str:
    """Generate ML code based on the problem type.
    
    Args:
        query: The user's query
        problem_type: Identified problem type
    
    Returns:
        Python code string
    """
    code_templates = {
        "delay_prediction": '''
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder

# Load the airline operations data
df = pd.read_csv('data/airline_operations.csv')

# Remove cancelled flights for delay prediction
df = df[~df['cancelled']].copy()

# Feature engineering
df['hour'] = pd.to_datetime(df['scheduled_departure']).dt.hour
df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
df['month'] = pd.to_datetime(df['date']).dt.month

# Encode categorical variables
le_airline = LabelEncoder()
le_origin = LabelEncoder()
le_dest = LabelEncoder()

df['airline_encoded'] = le_airline.fit_transform(df['airline'])
df['origin_encoded'] = le_origin.fit_transform(df['origin'])
df['dest_encoded'] = le_dest.fit_transform(df['destination'])

# Select features
features = ['airline_encoded', 'origin_encoded', 'dest_encoded', 
            'hour', 'day_of_week', 'month', 'turnaround_minutes', 'load_factor']
X = df[features]
y = df['delay_minutes']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Random Forest model
model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

# Make predictions
y_pred = model.predict(X_test)

# Evaluate
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print(f"Model Performance:")
print(f"  MAE: {mae:.2f} minutes")
print(f"  RMSE: {rmse:.2f} minutes")
print(f"  R² Score: {r2:.3f}")

# Feature importance
feature_importance = pd.DataFrame({
    'feature': features,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\\nFeature Importance:")
print(feature_importance)
''',
        "cancellation_prediction": '''
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import SMOTE

# Load the airline operations data
df = pd.read_csv('data/airline_operations.csv')

# Feature engineering
df['hour'] = pd.to_datetime(df['scheduled_departure']).dt.hour
df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
df['month'] = pd.to_datetime(df['date']).dt.month

# Encode categorical variables
le_airline = LabelEncoder()
le_origin = LabelEncoder()
le_dest = LabelEncoder()

df['airline_encoded'] = le_airline.fit_transform(df['airline'])
df['origin_encoded'] = le_origin.fit_transform(df['origin'])
df['dest_encoded'] = le_dest.fit_transform(df['destination'])

# Select features
features = ['airline_encoded', 'origin_encoded', 'dest_encoded', 
            'hour', 'day_of_week', 'month', 'turnaround_minutes']
X = df[features]
y = df['cancelled'].astype(int)

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Handle class imbalance with SMOTE
smote = SMOTE(random_state=42)
X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)

# Train Random Forest model with class weights
model = RandomForestClassifier(
    n_estimators=100, 
    max_depth=10, 
    class_weight='balanced',
    random_state=42, 
    n_jobs=-1
)
model.fit(X_train_balanced, y_train_balanced)

# Make predictions
y_pred = model.predict(X_test)
y_pred_proba = model.predict_proba(X_test)[:, 1]

# Evaluate
print("Classification Report:")
print(classification_report(y_test, y_pred, target_names=['Not Cancelled', 'Cancelled']))

print("\\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print(f"\\nROC-AUC Score: {roc_auc_score(y_test, y_pred_proba):.3f}")

# Feature importance
feature_importance = pd.DataFrame({
    'feature': features,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\\nFeature Importance:")
print(feature_importance)
''',
        "demand_forecasting": '''
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder

# Load the airline operations data
df = pd.read_csv('data/airline_operations.csv')

# Remove cancelled flights
df = df[~df['cancelled']].copy()

# Feature engineering for demand forecasting
df['date'] = pd.to_datetime(df['date'])
df['day_of_week'] = df['date'].dt.dayofweek
df['month'] = df['date'].dt.month
df['week_of_year'] = df['date'].dt.isocalendar().week
df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)

# Create route identifier
df['route'] = df['origin'] + '-' + df['destination']

# Encode categorical variables
le_airline = LabelEncoder()
le_route = LabelEncoder()

df['airline_encoded'] = le_airline.fit_transform(df['airline'])
df['route_encoded'] = le_route.fit_transform(df['route'])

# Calculate historical average load factor by route (lag feature)
route_avg_load = df.groupby('route')['load_factor'].transform('mean')
df['route_avg_load'] = route_avg_load

# Select features
features = ['airline_encoded', 'route_encoded', 'day_of_week', 
            'month', 'week_of_year', 'is_weekend', 'route_avg_load']
X = df[features]
y = df['load_factor']

# Split data (time-aware split would be better for production)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Gradient Boosting model
model = GradientBoostingRegressor(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=5,
    random_state=42
)
model.fit(X_train, y_train)

# Make predictions
y_pred = model.predict(X_test)

# Evaluate
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print(f"Load Factor Prediction Performance:")
print(f"  MAE: {mae:.3f}")
print(f"  RMSE: {rmse:.3f}")
print(f"  R² Score: {r2:.3f}")

# Feature importance
feature_importance = pd.DataFrame({
    'feature': features,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\\nFeature Importance:")
print(feature_importance)
''',
        "general_ml": '''
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, mean_absolute_error

# Load the airline operations data
df = pd.read_csv('data/airline_operations.csv')

# Basic feature engineering
df['hour'] = pd.to_datetime(df['scheduled_departure']).dt.hour
df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
df['month'] = pd.to_datetime(df['date']).dt.month

# Encode categorical variables
le_airline = LabelEncoder()
le_origin = LabelEncoder()
le_dest = LabelEncoder()

df['airline_encoded'] = le_airline.fit_transform(df['airline'])
df['origin_encoded'] = le_origin.fit_transform(df['origin'])
df['dest_encoded'] = le_dest.fit_transform(df['destination'])

# Example: Predict if flight will be delayed (>15 minutes)
df_active = df[~df['cancelled']].copy()
df_active['is_delayed'] = (df_active['delay_minutes'] >= 15).astype(int)

# Select features
features = ['airline_encoded', 'origin_encoded', 'dest_encoded', 
            'hour', 'day_of_week', 'month', 'turnaround_minutes', 'load_factor']
X = df_active[features]
y = df_active['is_delayed']

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

# Evaluate with cross-validation
cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
print(f"Cross-validation accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

# Test set evaluation
y_pred = model.predict(X_test)
print("\\nTest Set Performance:")
print(classification_report(y_test, y_pred, target_names=['On-Time', 'Delayed']))

# Feature importance
feature_importance = pd.DataFrame({
    'feature': features,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\\nFeature Importance:")
print(feature_importance)
'''
    }
    
    return code_templates.get(problem_type, code_templates["general_ml"]).strip()


def _formulate_ml_response(
    query: str, 
    problem_type: str, 
    recommendations: str, 
    code: str = None, 
    context: Dict[str, Any] = None
) -> str:
    """Formulate a comprehensive ML response.
    
    Args:
        query: The original query
        problem_type: Identified problem type
        recommendations: Model recommendations
        code: Generated code (if any)
        context: Optional conversation context
    
    Returns:
        Formatted response string
    """
    response_parts = []
    
    # Add problem understanding
    response_parts.append(f"**Problem Type:** {problem_type.replace('_', ' ').title()}")
    response_parts.append("")
    
    # Add recommendations
    response_parts.append(recommendations.strip())
    response_parts.append("")
    
    # Add code if generated
    if code:
        response_parts.append("**Implementation Example:**")
        response_parts.append("")
        response_parts.append("```python")
        response_parts.append(code)
        response_parts.append("```")
        response_parts.append("")
        response_parts.append("**Notes:**")
        response_parts.append("- Install required packages: `pip install pandas scikit-learn numpy imbalanced-learn`")
        response_parts.append("- Adjust hyperparameters based on your specific dataset and requirements")
        response_parts.append("- Consider using cross-validation for more robust evaluation")
        response_parts.append("- Monitor model performance over time and retrain as needed")
    
    return "\n".join(response_parts)
