"""Mixtrain SDK - ML Platform Client and Workflow Framework."""

import importlib.metadata

__version__ = importlib.metadata.version("mixtrain")

from .client import MixClient, MixFlow, MixModel, sandbox
from .datasets import Dataset, get_dataset, list_datasets
from .evaluations import Eval, get_eval, list_evals
from .files import FileInfo, Files, UploadDirResult, UploadError

# Utilities for workflows
from .helpers import (
    generate_name,
    install_packages,
    sanitize_model_name,
    validate_resource_name,
)

# Proxy classes for resources (lazy API access)
from .models import Model, get_model, list_models
from .result import BatchResult, ModelResult, RunStatus
from .routers import Router, get_router, list_routers

# Media and text types (explicit wrappers for outputs)
from .types import (
    JSON,
    Audio,
    Embedding,
    File,
    Image,
    MCAP,
    Markdown,
    MixType,
    Model3D,
    Rerun,
    Text,
    Video,
    deserialize_output,
    extract_output_schema,
    serialize_output,
)
from .workflows import Workflow, get_workflow, list_workflows

__all__ = [
    # Version
    "__version__",
    # Client and workflow
    "MixClient",
    "MixFlow",
    "MixModel",
    "sandbox",
    # Proxy classes (for accessing and creating resources)
    "Model",
    "ModelResult",
    "BatchResult",
    "RunStatus",
    "get_model",
    "list_models",
    "Eval",
    "get_eval",
    "list_evals",
    "Dataset",
    "get_dataset",
    "list_datasets",
    "Workflow",
    "get_workflow",
    "list_workflows",
    "Router",
    "get_router",
    "list_routers",
    # Files
    "Files",
    "FileInfo",
    "UploadDirResult",
    "UploadError",
    # Media and text types (explicit wrappers)
    "MixType",
    "File",
    "Image",
    "Video",
    "Audio",
    "Model3D",
    "MCAP",
    "Rerun",
    "Text",
    "Markdown",
    "JSON",
    "Embedding",
    # Serialization
    "serialize_output",
    "deserialize_output",
    "extract_output_schema",
    # Utilities
    "sanitize_model_name",
    "generate_name",
    "install_packages",
    "validate_resource_name",
]
