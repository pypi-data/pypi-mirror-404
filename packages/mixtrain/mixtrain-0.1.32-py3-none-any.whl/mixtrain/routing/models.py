"""Pydantic models for routing configuration."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, validator


class RoutingStrategy(str, Enum):
    """Available routing strategies."""

    SINGLE = "single"  # Route to single model
    SPLIT = "split"  # Split traffic between multiple models (A/B testing)
    SHADOW = "shadow"  # Primary + shadow routing
    FALLBACK = "fallback"  # Try primary, fallback to secondary on failure


class ConditionOperator(str, Enum):
    """Condition operators for rule evaluation."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    REGEX = "regex"


class RoutingCondition(BaseModel):
    """A condition for rule evaluation."""

    field: str = Field(
        description="Field path to evaluate (e.g., 'user.tier', 'request.type')"
    )
    operator: ConditionOperator = Field(description="Comparison operator")
    value: str | int | float | bool | list[Any] | None = Field(
        None, description="Expected value for comparison"
    )
    description: str | None = Field(
        None, description="Human-readable condition description"
    )

    class Config:
        use_enum_values = True


class RoutingTarget(BaseModel):
    """A target model for routing."""

    provider: str = Field(description="Model provider (e.g., 'modal', 'fal', 'custom')")
    model_name: str = Field(description="Name of the model")
    endpoint: str = Field(description="Model endpoint URL")
    weight: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Routing weight (0.0-1.0)"
    )
    label: str | None = Field(None, description="Optional label for this target")
    timeout_ms: int | None = Field(None, ge=100, description="Timeout in milliseconds")
    retry_count: int | None = Field(None, ge=0, le=5, description="Number of retries")

    # Provider-specific fields
    function_name: str | None = Field(
        None, description="Function name for Modal provider"
    )
    request_class: str | None = Field(
        None, description="Request class for Modal provider"
    )
    headers: dict[str, str] | None = Field(None, description="Custom HTTP headers")

    # Runtime fields
    is_shadow: bool = Field(
        default=False, description="Whether this is a shadow target"
    )

    @validator("weight")
    def validate_weight(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError("Weight must be between 0.0 and 1.0")
        return v

    class Config:
        use_enum_values = True


class RoutingRule(BaseModel):
    """A routing rule with conditions and targets."""

    name: str = Field(description="Name of the routing rule")
    description: str | None = Field(
        "", description="Description of what this rule does"
    )
    priority: int = Field(
        default=0, description="Priority (higher values evaluated first)"
    )
    is_enabled: bool = Field(default=True, description="Whether this rule is active")
    conditions: list[RoutingCondition] = Field(
        default_factory=list, description="Conditions for this rule"
    )
    strategy: RoutingStrategy = Field(
        default=RoutingStrategy.SINGLE, description="Routing strategy"
    )
    targets: list[RoutingTarget] = Field(description="Target models for routing")

    @validator("targets")
    def validate_targets(cls, v, values):
        if not v:
            raise ValueError("At least one target must be specified")

        strategy = values.get("strategy")
        if strategy == RoutingStrategy.SPLIT:
            total_weight = sum(target.weight for target in v)
            if abs(total_weight - 1.0) > 0.001:  # Allow small floating point errors
                raise ValueError("Split strategy requires target weights to sum to 1.0")
        elif strategy == RoutingStrategy.SHADOW:
            if len(v) != 2:
                raise ValueError(
                    "Shadow strategy requires exactly 2 targets (primary and shadow)"
                )

        return v

    class Config:
        use_enum_values = True


class RoutingConfig(BaseModel):
    """Complete routing configuration with metadata."""

    name: str = Field(description="Name of the routing configuration")
    description: str | None = Field("", description="Description of this configuration")
    rules: list[RoutingRule] = Field(description="Routing rules")
    metadata: dict[str, Any] | None = Field(
        default_factory=dict, description="Additional metadata"
    )

    @validator("rules")
    def validate_rules(cls, v):
        if not v:
            raise ValueError("At least one routing rule must be specified")
        return v

    @classmethod
    def from_json(cls, config_json: dict[str, Any]) -> "RoutingConfig":
        """Create RoutingConfig from JSON dictionary."""
        return cls(**config_json)

    def to_json(self) -> dict[str, Any]:
        """Convert RoutingConfig to JSON dictionary using standard format."""
        return self.dict()

    class Config:
        use_enum_values = True


class RoutingResult(BaseModel):
    """Result of routing evaluation."""

    matched_rule: RoutingRule | None = Field(None, description="The matched rule")
    selected_targets: list[RoutingTarget] = Field(description="Selected targets")
    explanation: str = Field(
        description="Human-readable explanation of the routing decision"
    )
    execution_time_ms: float | None = Field(
        None, description="Time taken for routing decision"
    )
    metadata: dict[str, Any] | None = Field(
        default_factory=dict, description="Additional result metadata"
    )

    class Config:
        use_enum_values = True


class TestRequest(BaseModel):
    """Request for testing routing logic."""

    request_data: dict[str, Any] = Field(
        description="Sample request data to test routing against"
    )
    expected_rule: str | None = Field(
        None, description="Expected rule name for validation"
    )

    class Config:
        use_enum_values = True
