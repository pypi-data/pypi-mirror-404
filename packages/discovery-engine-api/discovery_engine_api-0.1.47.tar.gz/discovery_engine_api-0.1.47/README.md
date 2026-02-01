# Discovery Engine Python API

The Discovery Engine Python API provides a simple programmatic interface to run analyses via Python, offering an alternative to using the web dashboard. Instead of uploading datasets and configuring analyses through the UI, you can automate your discovery workflows directly from your Python code or scripts.

All analyses run through the API are fully integrated with your Discovery Engine account. Results are automatically displayed in the dashboard, where you can view detailed reports, explore patterns, and share findings with your team. Your account management, credit balance, and subscription settings are all handled through the dashboard.

## Installation

```bash
pip install discovery-engine-api
```

For pandas DataFrame support:

```bash
pip install discovery-engine-api[pandas]
```

For Jupyter notebook support:

```bash
pip install discovery-engine-api[jupyter]
```

This installs `nest-asyncio`, which is required to use `engine.run()` in Jupyter notebooks. Alternatively, you can use `await engine.run_async()` directly in Jupyter notebooks without installing the jupyter extra.

## Configuration

### API Keys

Get your API key from the [Developers page](https://disco.leap-labs.com/developers) in your Discovery Engine dashboard.

## Quick Start

```python
from discovery import Engine

# Initialize engine
engine = Engine(api_key="your-api-key")

# Run analysis on a dataset and wait for results
result = engine.run(
    file="data.csv",
    target_column="diagnosis",
    mode="fast",
    description="Rare diseases dataset",
    excluded_columns=["patient_id"],  # Exclude ID column from analysis
    wait=True  # Wait for completion and return full results
)

print(f"Run ID: {result.run_id}")
print(f"Status: {result.status}")
print(f"Found {len(result.patterns)} patterns")
```


## Examples

### Working with Pandas DataFrames

```python
import pandas as pd
from discovery import Engine

df = pd.read_csv("data.csv")
# or create DataFrame directly

engine = Engine(api_key="your-api-key")
result = engine.run(
    file=df,  # Pass DataFrame directly
    target_column="outcome",
    column_descriptions={
        "age": "Patient age in years",
        "heart rate": None
    },
    excluded_columns=["id", "timestamp"],  # Exclude ID and timestamp columns from analysis
    wait=True
)
```


### Async Workflow

```python
import asyncio
from discovery import Engine

async def run_analysis():
    async with Engine(api_key="your-api-key") as engine:
        # Start analysis without waiting
        result = await engine.run_async(
            file="data.csv",
            target_column="target",
            wait=False
        )
        print(f"Started run: {result.run_id}")

        # Later, get results
        result = await engine.get_results(result.run_id)
        
        # Or wait for completion
        result = await engine.wait_for_completion(result.run_id, timeout=1200)
        return result

result = asyncio.run(run_analysis())
```

### Using in Jupyter Notebooks

In Jupyter notebooks, you have two options:

**Option 1: Install the jupyter extra (recommended)**
```bash
pip install discovery-engine-api[jupyter]
```

Then use `engine.run()` as normal:
```python
from discovery import Engine

engine = Engine(api_key="your-api-key")
result = engine.run(file="data.csv", target_column="target", wait=True)
```

**Option 2: Use async directly**
```python
from discovery import Engine

engine = Engine(api_key="your-api-key")
result = await engine.run_async(file="data.csv", target_column="target", wait=True)
```


## Configuration Options

The `run()` and `run_async()` methods accept the following parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file` | `str`, `Path`, or `DataFrame` | **Required** | Dataset file path or pandas DataFrame |
| `target_column` | `str` | **Required** | Name of column to predict |
| `mode` | `"fast"` / `"deep"` | `"fast"` | Analysis depth |
| `title` | `str` | `None` | Optional dataset title |
| `description` | `str` | `None` | Optional dataset description |
| `column_descriptions` | `Dict[str, str]` | `None` | Optional column name -> description mapping |
| `excluded_columns` | `List[str]` | `None` | Optional list of column names to exclude from analysis (e.g., IDs, timestamps) |
| `visibility` | `"public"` / `"private"` | `"public"` | Dataset visibility (private requires credits) |
| `auto_report_use_llm_evals` | `bool` | `True` | Use LLM for pattern descriptions |
| `author` | `str` | `None` | Optional dataset author attribution |
| `source_url` | `str` | `None` | Optional source URL for dataset attribution |
| `wait` | `bool` | `False` | Wait for analysis to complete and return full results |
| `wait_timeout` | `float` | `None` | Maximum seconds to wait for completion (only if `wait=True`) |


## Credits and Pricing

If you don't have enough credits for a private run, the SDK will raise an `httpx.HTTPStatusError` with an error message like:
```
Insufficient credits. You need X credits but only have Y available.
```

**Solutions:**
1. Make your dataset public (set `visibility="public"`) - completely free
2. Visit [https://disco.leap-labs.com/account](https://disco.leap-labs.com/account) to:
   - Purchase additional credits
   - Upgrade to a subscription plan that includes more credits


## Return Value

The `run()` and `run_async()` methods return an `EngineResult` object with the following fields:

### EngineResult

```python
@dataclass
class EngineResult:
    # Identifiers
    run_id: str                    # Unique run identifier
    report_id: Optional[str]       # Report ID (if report created)
    status: str                    # "pending", "processing", "completed", "failed"
    
    # Dataset metadata
    dataset_title: Optional[str]           # Dataset title
    dataset_description: Optional[str]    # Dataset description
    total_rows: Optional[int]              # Number of rows in dataset
    target_column: Optional[str]           # Name of target column
    task: Optional[str]                    # "regression", "binary_classification", or "multiclass_classification"
    
    # LLM-generated summary
    summary: Optional[Summary]             # Summary object with overview, insights, etc.
    
    # Discovered patterns
    patterns: List[Pattern]                 # List of discovered patterns
    
    # Column/feature information
    columns: List[Column]                  # List of columns with statistics and importance
    
    # Correlation matrix
    correlation_matrix: List[CorrelationEntry]  # Feature correlations
    
    # Global feature importance
    feature_importance: Optional[FeatureImportance]  # Feature importance scores
    
    # Job tracking
    job_id: Optional[str]           # Job ID for tracking processing
    job_status: Optional[str]      # Job status
    error_message: Optional[str]   # Error message if analysis failed
```

### Summary

```python
@dataclass
class Summary:
    overview: str                          # High-level explanation of findings
    key_insights: List[str]                # List of main takeaways
    novel_patterns: PatternGroup           # Novel pattern explanations
    surprising_findings: PatternGroup      # Surprising findings
    statistically_significant: PatternGroup  # Statistically significant patterns
    data_insights: Optional[DataInsights]  # Important features, correlations
    selected_pattern_id: Optional[str]     # ID of selected pattern
```

### Pattern

```python
@dataclass
class Pattern:
    id: str                                # Pattern identifier
    task: str                              # Task type
    target_column: str                     # Target column name
    direction: str                         # "min" or "max"
    p_value: float                         # Statistical p-value
    conditions: List[Dict]                 # Pattern conditions (continuous, categorical, datetime)
    lift_value: float                      # Lift value (how much the pattern increases/decreases target)
    support_count: int                     # Number of rows matching pattern
    support_percentage: float              # Percentage of rows matching pattern
    pattern_type: str                      # "validated" or "speculative"
    novelty_type: str                      # "novel" or "confirmatory"
    target_score: float                    # Target score for this pattern
    description: str                       # Human-readable description
    novelty_explanation: str               # Explanation of novelty
    target_class: Optional[str]            # Target class (for classification)
    target_mean: Optional[float]           # Target mean (for regression)
    target_std: Optional[float]            # Target standard deviation
    citations: List[Dict]                  # Academic citations
```

### Column

```python
@dataclass
class Column:
    id: str                                # Column identifier
    name: str                              # Column name
    display_name: str                      # Display name
    type: str                              # "continuous" or "categorical"
    data_type: str                         # "int", "float", "string", "boolean", "datetime"
    enabled: bool                          # Whether column is enabled
    description: Optional[str]              # Column description
    
    # Statistics
    mean: Optional[float]                  # Mean value
    median: Optional[float]                 # Median value
    std: Optional[float]                   # Standard deviation
    min: Optional[float]                   # Minimum value
    max: Optional[float]                   # Maximum value
    iqr_min: Optional[float]               # IQR minimum
    iqr_max: Optional[float]               # IQR maximum
    mode: Optional[str]                    # Mode value
    approx_unique: Optional[int]           # Approximate unique count
    null_percentage: Optional[float]      # Percentage of null values
    
    # Feature importance
    feature_importance_score: Optional[float]  # Feature importance score
```

### FeatureImportance

```python
@dataclass
class FeatureImportance:
    kind: str                              # Feature importance type: "global" 
    baseline: float                        # Baseline model output
    scores: List[FeatureImportanceScore]   # List of feature scores
```

### CorrelationEntry

```python
@dataclass
class CorrelationEntry:
    feature_x: str                         # First feature name
    feature_y: str                         # Second feature name
    value: float                           # Correlation value (-1 to 1)
```

### Pattern

```python
@dataclass
class Pattern:
    id: str
    task: str
    target_column: str
    direction: str  # "min" or "max"
    p_value: float
    conditions: List[Dict]  # Continuous, categorical, or datetime conditions
    lift_value: float
    support_count: int
    support_percentage: float
    pattern_type: str  # "validated" or "speculative"
    novelty_type: str  # "novel" or "confirmatory"
    target_score: float
    description: str
    novelty_explanation: str
    target_class: Optional[str]
    target_mean: Optional[float]
    target_std: Optional[float]
    citations: List[Dict]
```

