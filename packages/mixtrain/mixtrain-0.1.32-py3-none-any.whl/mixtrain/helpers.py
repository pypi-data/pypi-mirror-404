"""Common utilities for mixtrain workflows.

This module provides helper functions commonly needed in workflow code,
reducing boilerplate in examples and user code.
"""

import re
import subprocess
import sys
from datetime import datetime

# Resource name validation pattern (matches backend slug validation)
# Names must: start with lowercase letter, contain only lowercase letters,
# numbers, hyphens, or underscores, and be 1-63 characters long.
NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,62}$")


def validate_resource_name(name: str, resource_type: str = "resource") -> None:
    """Validate a resource name against the slug pattern.

    Args:
        name: Name to validate
        resource_type: Type of resource for error message (e.g., "model", "workflow")

    Raises:
        ValueError: If name is invalid

    Example:
        >>> validate_resource_name("my-model", "model")  # OK
        >>> validate_resource_name("My Model", "model")  # Raises ValueError
    """
    if not NAME_PATTERN.match(name):
        raise ValueError(
            f"Invalid {resource_type} name: '{name}'. Must start with lowercase letter, "
            "contain only lowercase letters, numbers, hyphens, or underscores, "
            "and be 1-63 characters long."
        )


def sanitize_model_name(model_name: str) -> str:
    """Convert model name to a valid column/identifier name.

    Removes provider prefixes and converts special characters to underscores.

    Args:
        model_name: Full model name (e.g., "flux-pro")

    Returns:
        Sanitized name suitable for column names (e.g., "flux_pro")

    Example:
        >>> sanitize_model_name("flux-pro")
        'flux_pro'
        >>> sanitize_model_name("modal/my-model")
        'my_model'
    """
    return (
        model_name.replace("fal-ai/", "")
        .replace("modal/", "")
        .replace("openai/", "")
        .replace("anthropic/", "")
        .replace("/", "_")
        .replace("-", "_")
    )


def generate_name(prefix: str, suffix: str = "") -> str:
    """Generate a unique name with current date.

    Useful for creating dataset and evaluation names that include timestamps.
    Hyphens are automatically converted to underscores for valid resource names.

    Args:
        prefix: Name prefix (e.g., "t2i", "image-caption")
        suffix: Optional suffix before date (e.g., "eval", "results")

    Returns:
        Name with date (e.g., "t2i_eval_dec_29_2025", "image_caption_results_jan_02_2026")

    Example:
        >>> generate_name("t2i", "eval")  # Returns "t2i_eval_dec_29_2025"
        >>> generate_name("image-caption", "results")  # Returns "image_caption_results_dec_29_2025"
    """
    # Replace hyphens with underscores for valid resource names
    prefix = prefix.replace("-", "_")
    suffix = suffix.replace("-", "_") if suffix else ""
    date_str = datetime.now().strftime("%b_%d_%Y").lower()
    if suffix:
        return f"{prefix}_{suffix}_{date_str}"
    return f"{prefix}_{date_str}"


def install_packages(*packages: str) -> None:
    """Install Python packages at runtime.

    Useful for installing dependencies in workflow sandboxes that may not
    have all required packages pre-installed.

    Args:
        *packages: Package names to install (e.g., "fal-client", "pillow")

    Example:
        >>> install_packages("fal-client", "pydantic<=2.11.10")
    """
    if not packages:
        return
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", *packages],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"Successfully installed: {', '.join(packages)}")
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        raise
