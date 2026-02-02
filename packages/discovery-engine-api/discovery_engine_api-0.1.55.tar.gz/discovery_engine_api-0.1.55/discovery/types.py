"""Type definitions for the Discovery SDK."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Union


@dataclass
class FileInfo:
    """Information about an uploaded file."""

    file_path: str  # GCS path
    file_hash: str
    file_size: int
    mime_type: str


@dataclass
class TimeseriesGroup:
    """Timeseries column group metadata."""

    base_name: str
    columns: List[str]
    num_timesteps: int
    pattern_matched: str
    dtype: str  # "numeric" or "categorical"


# Pattern types


@dataclass
class PatternContinuousCondition:
    """A continuous condition in a pattern."""

    type: Literal["continuous"]
    feature: str
    min_value: float
    max_value: float
    min_q: Optional[float] = None
    max_q: Optional[float] = None


@dataclass
class PatternCategoricalCondition:
    """A categorical condition in a pattern."""

    type: Literal["categorical"]
    feature: str
    values: List[Union[str, int, float, bool, None]]


@dataclass
class PatternDatetimeCondition:
    """A datetime condition in a pattern."""

    type: Literal["datetime"]
    feature: str
    min_value: float  # epoch milliseconds
    max_value: float  # epoch milliseconds
    min_datetime: str  # human-readable
    max_datetime: str  # human-readable
    min_q: Optional[float] = None
    max_q: Optional[float] = None


PatternCondition = Union[
    PatternContinuousCondition, PatternCategoricalCondition, PatternDatetimeCondition
]


@dataclass
class PatternCitation:
    """Academic citation for a pattern."""

    url: str
    title: Optional[str] = None
    doi: Optional[str] = None
    authors: Optional[List[str]] = None
    year: Optional[str] = None
    journal: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None


@dataclass
class Pattern:
    """A discovered pattern in the data."""

    id: str
    task: str  # regression, binary_classification, multiclass_classification
    target_column: str
    direction: str  # "min" or "max"
    p_value: float
    conditions: List[Dict[str, Any]]  # PatternCondition as dicts
    lift_value: float
    support_count: int
    support_percentage: float
    pattern_type: str  # "validated" or "speculative"
    novelty_type: str  # "novel" or "confirmatory"
    target_score: float
    description: str
    novelty_explanation: str
    target_class: Optional[str] = None
    target_mean: Optional[float] = None
    target_std: Optional[float] = None
    citations: List[Dict[str, Any]] = field(default_factory=list)


# Column/Feature types


@dataclass
class Column:
    """Information about a dataset column/feature."""

    id: str
    name: str
    display_name: str
    type: str  # "continuous" or "categorical"
    data_type: str  # "int", "float", "string", "boolean", "datetime"
    enabled: bool
    description: Optional[str] = None

    # Statistics
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    iqr_min: Optional[float] = None
    iqr_max: Optional[float] = None
    mode: Optional[str] = None
    approx_unique: Optional[int] = None
    null_percentage: Optional[float] = None

    # Feature importance
    feature_importance_score: Optional[float] = None


# Summary types (LLM-generated)


@dataclass
class DataInsights:
    """LLM-generated data insights."""

    important_features: List[str]
    important_features_explanation: str
    strong_correlations: List[Dict[str, str]]  # [{"feature1": "...", "feature2": "..."}]
    strong_correlations_explanation: str
    notable_relationships: List[str]


@dataclass
class PatternGroup:
    """A group of patterns with explanation."""

    pattern_ids: List[str]
    explanation: str


@dataclass
class Summary:
    """LLM-generated summary of the analysis."""

    overview: str
    key_insights: List[str]
    novel_patterns: PatternGroup
    surprising_findings: PatternGroup
    statistically_significant: PatternGroup
    data_insights: DataInsights
    selected_pattern_id: Optional[str] = None


# Feature importance types


@dataclass
class FeatureImportanceScore:
    """A single feature importance score."""

    feature: str
    score: float


@dataclass
class FeatureImportance:
    """Global feature importance information."""

    kind: str  # "global" or "local"
    baseline: float  # expected model output
    scores: List[FeatureImportanceScore]


# Correlation matrix types


@dataclass
class CorrelationEntry:
    """A single correlation matrix entry."""

    feature_x: str
    feature_y: str
    value: float


# Main result type


@dataclass
class EngineResult:
    """Complete result of an engine run."""

    # Identifiers
    run_id: str
    report_id: Optional[str] = None
    status: str = "pending"  # pending, processing, completed, failed

    # Dataset metadata
    dataset_title: Optional[str] = None
    dataset_description: Optional[str] = None
    total_rows: Optional[int] = None
    target_column: Optional[str] = None
    task: Optional[str] = None  # regression, binary_classification, multiclass_classification

    # LLM-generated summary
    summary: Optional[Summary] = None

    # Discovered patterns
    patterns: List[Pattern] = field(default_factory=list)

    # Column/feature information with stats and importance
    columns: List[Column] = field(default_factory=list)

    # Correlation matrix
    correlation_matrix: List[CorrelationEntry] = field(default_factory=list)

    # Global feature importance
    feature_importance: Optional[FeatureImportance] = None

    # Job tracking
    job_id: Optional[str] = None
    job_status: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class RunStatus:
    """Status of a run."""

    run_id: str
    status: str
    job_id: Optional[str] = None
    job_status: Optional[str] = None
    error_message: Optional[str] = None
