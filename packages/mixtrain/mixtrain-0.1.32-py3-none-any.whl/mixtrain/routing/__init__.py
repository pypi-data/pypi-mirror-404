"""
Mixtrain Routing Engine

A standalone routing engine for intelligent model selection and traffic management.
Supports multiple routing strategies, conditional logic, and provider-agnostic configuration.

Note: RoutingEngine is internal. Use the Router proxy class for routing operations:
    >>> from mixtrain import get_router
    >>> router = get_router("my-router")
    >>> result = router.route({"user": {"tier": "premium"}})
"""

# RoutingEngine is internal - import directly from .engine if needed for CLI/tests
from .builder import ConfigBuilder, RuleBuilder
from .exceptions import (
    ConditionEvaluationError,
    ConfigurationError,
    RoutingConfigValidationError,
    RoutingError,
    TargetSelectionError,
)
from .models import (
    ConditionOperator,
    RoutingCondition,
    RoutingConfig,
    RoutingResult,
    RoutingRule,
    RoutingStrategy,
    RoutingTarget,
)
from .validator import ConfigurationLinter, RoutingValidator

__all__ = [
    # Validator and linter (for config validation)
    "RoutingValidator",
    "ConfigurationLinter",
    # Configuration models
    "RoutingConfig",
    "RoutingRule",
    "RoutingCondition",
    "RoutingTarget",
    "RoutingResult",
    # Enums
    "RoutingStrategy",
    "ConditionOperator",
    # Builder pattern
    "ConfigBuilder",
    "RuleBuilder",
    # Exceptions
    "RoutingError",
    "ConfigurationError",
    "RoutingConfigValidationError",
    "TargetSelectionError",
    "ConditionEvaluationError",
]

__version__ = "0.1.0"
