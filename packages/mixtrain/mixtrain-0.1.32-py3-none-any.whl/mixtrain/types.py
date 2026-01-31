"""MixType - Typed values for workflow and model inputs/outputs.

This module provides type classes that enable rich rendering in the UI.
When workflows or models return typed values, the frontend can render
them appropriately (images, videos, links to resources, etc.).
"""

from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Iterator,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

if TYPE_CHECKING:
    import numpy as np
    import PIL.Image
    import cv2


@dataclass
class MixType:
    """Base class for typed values. Used for both inputs and outputs.

    Subclasses define specific types with their own `_type` identifier
    that tells the frontend how to render the value.
    """

    _type: str = field(default="", init=False)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        result = {}
        for k, v in self.__dict__.items():
            if k.startswith("_"):
                result[k] = v
            else:
                result[k] = v
        return result


# =============================================================================
# File Type - Base class for all media/file references
# =============================================================================


@dataclass
class File(MixType):
    """Base class for file references. Provides to_file() for all media types.

    Can be used directly for generic file references, or subclassed by
    Image, Video, Audio for type-specific helpers.

    Args:
        url: URL to the file (https://, gs://, s3://)
        content_type: Optional MIME type
        filename: Optional original filename

    Example:
        >>> return {"data": File(url="gs://bucket/data.bin")}
    """

    url: str
    content_type: str | None = None
    filename: str | None = None
    _type: str = field(default="file", init=False)
    _local_path: str | None = field(default=None, init=False, repr=False)

    def to_file(self, path: str | None = None) -> str:
        """Download to local file (cached). Returns path.

        Uses Files.download() which handles gs://, s3://, and https:// URLs,
        getting presigned URLs from backend as needed.

        Args:
            path: Optional path to save to. If not provided, uses a temp file.

        Returns:
            Path to the downloaded file.
        """
        # Return cached path if available and no specific path requested
        if self._local_path and path is None:
            import os

            if os.path.exists(self._local_path):
                return self._local_path

        from .files import Files

        # Generate temp path if not provided
        if path is None:
            import os
            import tempfile
            from urllib.parse import urlparse

            ext = os.path.splitext(urlparse(self.url).path)[1] or ""
            fd, path = tempfile.mkstemp(suffix=ext)
            os.close(fd)

        # Files.download() handles presigned URLs for gs://s3://
        Files().download(self.url, path)

        # Cache the path if we generated it
        if self._local_path is None:
            object.__setattr__(self, "_local_path", path)

        return path


# =============================================================================
# Media Types - Render content inline
# =============================================================================


@dataclass
class Image(File):
    """An image file. Extends File with image-specific helpers.

    Args:
        url: URL to the image (https://, gs://, s3://)
        width: Optional width in pixels
        height: Optional height in pixels
        format: Optional format (png, jpg, webp)

    Example:
        >>> # As output:
        >>> return {"image": Image(url="https://...", width=1024, height=1024)}
        >>> # As input in model run():
        >>> def run(self, image: Image):
        ...     pil_img = image.to_pil()  # Downloads and opens
    """

    url: str
    width: int | None = None
    height: int | None = None
    format: str | None = None
    _type: str = field(default="image", init=False)

    def to_pil(self) -> "PIL.Image.Image":
        """Return as PIL Image object.

        Downloads the image if needed and opens it with PIL.
        """
        from PIL import Image as PILImage

        return PILImage.open(self.to_file())

    def to_numpy(self) -> "np.ndarray":
        """Return as numpy array (H, W, C).

        Downloads the image if needed and converts to numpy array.
        """
        import numpy as np

        return np.array(self.to_pil())


@dataclass
class Video(File):
    """A video file. Extends File with video-specific helpers.

    Args:
        url: URL to the video (https://, gs://, s3://)
        duration_seconds: Optional duration in seconds
        width: Optional width in pixels
        height: Optional height in pixels
        format: Optional format (mp4, webm)

    Example:
        >>> # As output:
        >>> return {"video": Video(url="https://...", duration_seconds=5.0)}
        >>> # As input in model run():
        >>> def run(self, video: Video):
        ...     for frame in video.to_frames():
        ...         process(frame)
    """

    url: str
    duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None
    format: str | None = None
    _type: str = field(default="video", init=False)

    def to_cv2(self) -> "cv2.VideoCapture":
        """Return as OpenCV VideoCapture object.

        Downloads the video if needed and opens it with cv2.
        """
        import cv2

        return cv2.VideoCapture(self.to_file())

    def to_frames(self) -> Iterator["np.ndarray"]:
        """Yield frames as numpy arrays (H, W, C) in BGR format.

        Downloads the video if needed and iterates through frames.
        """
        import cv2

        cap = cv2.VideoCapture(self.to_file())
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                yield frame
        finally:
            cap.release()


@dataclass
class Audio(File):
    """An audio file. Extends File with audio-specific helpers.

    Args:
        url: URL to the audio file (https://, gs://, s3://)
        duration_seconds: Optional duration in seconds
        format: Optional format (mp3, wav)

    Example:
        >>> # As output:
        >>> return {"audio": Audio(url="https://...", duration_seconds=30.0)}
        >>> # As input in model run():
        >>> def run(self, audio: Audio):
        ...     samples, sr = audio.to_numpy()
    """

    url: str
    duration_seconds: float | None = None
    format: str | None = None
    _type: str = field(default="audio", init=False)

    def to_numpy(self) -> tuple["np.ndarray", int]:
        """Return as (samples array, sample_rate) using soundfile.

        Downloads the audio if needed and loads it with soundfile.

        Returns:
            Tuple of (samples as numpy array, sample rate as int)
        """
        import soundfile as sf

        data, samplerate = sf.read(self.to_file())
        return data, samplerate


@dataclass
class Model3D(MixType):
    """A 3D model to render with a viewer.

    Args:
        url: URL to the 3D model file
        format: Optional format (glb, gltf, obj)

    Example:
        >>> return {"model": Model3D(url="https://...", format="glb")}
    """

    url: str
    format: str | None = None
    _type: str = field(default="3d", init=False)


@dataclass
class MCAP(File):
    """An MCAP robotics log file. Opens in Foxglove viewer.

    MCAP is a container format for multimodal robotics data including
    sensor data, point clouds, images, robot state, and more.

    Args:
        url: URL to the MCAP file (https://, gs://, s3://)
        duration_ms: Optional duration in milliseconds

    Example:
        >>> return {"recording": MCAP(url="https://...", duration_ms=30000)}
        >>> # Set column type for dataset:
        >>> dataset.set_column_types({"trajectory": MCAP})
    """

    url: str
    duration_ms: int | None = None
    _type: str = field(default="mcap", init=False)


@dataclass
class Rerun(File):
    """A Rerun recording file (.rrd). Opens in Rerun viewer.

    Rerun is a visualization tool for multimodal data including
    3D point clouds, images, time series, and more.

    Args:
        url: URL to the .rrd file (https://, gs://, s3://)
        duration_ms: Optional duration in milliseconds

    Example:
        >>> return {"visualization": Rerun(url="https://...", duration_ms=30000)}
        >>> # Set column type for dataset:
        >>> dataset.set_column_types({"recording": Rerun})
    """

    url: str
    duration_ms: int | None = None
    _type: str = field(default="rrd", init=False)


# =============================================================================
# Text Types
# =============================================================================


@dataclass
class Text(MixType):
    """Plain text content.

    Args:
        content: The text content

    Example:
        >>> return {"message": Text(content="Processing complete!")}
    """

    content: str
    _type: str = field(default="text", init=False)


@dataclass
class Markdown(MixType):
    """Markdown content - renders with formatting.

    Args:
        content: The markdown content

    Example:
        >>> return {"report": Markdown(content="# Results\\n- Item 1\\n- Item 2")}
    """

    content: str
    _type: str = field(default="markdown", init=False)


@dataclass
class JSON(MixType):
    """JSON data - renders with syntax highlighting.

    Args:
        data: The JSON-serializable data (dict or list)

    Example:
        >>> return {"config": JSON(data={"key": "value", "items": [1, 2, 3]})}
    """

    data: dict | list
    _type: str = field(default="json", init=False)


@dataclass
class Embedding(MixType):
    """An embedding vector for ML features or semantic representations.

    Args:
        values: The embedding vector as a list of floats
        dimension: Optional dimension hint (auto-calculated if not provided)
        model: Optional name of the model that generated this embedding

    Example:
        >>> return {"embedding": Embedding(values=[0.1, 0.2, ...], model="text-embedding-3-small")}
    """

    values: list[float]
    dimension: int | None = None
    model: str | None = None
    _type: str = field(default="embedding", init=False)


# =============================================================================
# Serialization Functions
# =============================================================================


def _is_proxy_class(value: Any) -> tuple[bool, str | None, dict | None]:
    """Check if value is a proxy class instance and return type info.

    Returns:
        Tuple of (is_proxy, type_name, serialized_dict)
    """
    # Lazy imports to avoid circular dependencies
    from .datasets import Dataset as DatasetProxy
    from .evaluations import Eval
    from .models import Model as ModelProxy
    from .workflows import Workflow as WorkflowProxy

    if isinstance(value, ModelProxy):
        return (True, "model", {"_type": "model", "name": value.name})
    if isinstance(value, Eval):
        return (True, "evaluation", {"_type": "evaluation", "name": value.name})
    if isinstance(value, DatasetProxy):
        return (True, "dataset", {"_type": "dataset", "name": value.name})
    if isinstance(value, WorkflowProxy):
        result = {"_type": "workflow", "name": value.name}
        if value.run_number is not None:
            result["run_number"] = value.run_number
        return (True, "workflow", result)
    return (False, None, None)


def serialize_output(value: Any) -> dict | list | Any:
    """Serialize an output value with type information (recursive).

    Converts MixType instances, proxy classes, and nested structures into
    JSON-serializable dictionaries with `_type` fields for frontend rendering.

    Supports both explicit MixType wrappers (Image, Video, etc.) and proxy
    classes (Model, Eval, Dataset, Workflow) returned directly from SDK calls.

    Args:
        value: The value to serialize (MixType, proxy class, dict, list, or primitive)

    Returns:
        Serialized value with type information

    Example:
        >>> serialize_output(Image(url="https://..."))
        {'_type': 'image', 'url': 'https://...'}

        >>> serialize_output([Image(url="a"), Image(url="b")])
        {'_type': 'list', 'data': [{'_type': 'image', 'url': 'a'}, ...]}

        >>> from mixtrain import Eval
        >>> serialize_output(Eval("my-eval"))
        {'_type': 'evaluation', 'name': 'my-eval'}
    """
    # Check for proxy classes first
    is_proxy, _, serialized = _is_proxy_class(value)
    if is_proxy:
        return serialized

    if isinstance(value, MixType):
        # Serialize MixType instance
        result = {"_type": value._type}
        for k, v in value.__dict__.items():
            if not k.startswith("_") and v is not None:
                result[k] = serialize_output(v)
        return result
    elif isinstance(value, dict):
        # Check if any values are MixType instances or proxy classes
        has_typed_values = any(
            isinstance(v, MixType) or _is_proxy_class(v)[0] for v in value.values()
        )
        if has_typed_values:
            return {
                "_type": "dict",
                "data": {k: serialize_output(v) for k, v in value.items()},
            }
        else:
            # Plain dict - serialize recursively but don't wrap
            return {k: serialize_output(v) for k, v in value.items()}
    elif isinstance(value, list):
        # Check if any items are MixType instances or proxy classes
        has_typed_items = any(
            isinstance(v, MixType) or _is_proxy_class(v)[0] for v in value
        )
        if has_typed_items:
            return {"_type": "list", "data": [serialize_output(v) for v in value]}
        else:
            # Plain list - serialize recursively but don't wrap
            return [serialize_output(v) for v in value]
    else:
        # Primitive value - return as-is
        return value


def deserialize_output(data: Any) -> Any:
    """Deserialize typed output back to proxy classes or MixType objects (recursive).

    Args:
        data: Serialized data with _type fields

    Returns:
        Deserialized value (proxy class, MixType instance, dict, list, or primitive)
    """
    if not isinstance(data, dict):
        if isinstance(data, list):
            return [deserialize_output(v) for v in data]
        return data

    _type = data.get("_type")
    if _type is None:
        # Plain dict without type info
        return {k: deserialize_output(v) for k, v in data.items()}

    # Handle dict and list containers
    if _type == "dict":
        return {k: deserialize_output(v) for k, v in data.get("data", {}).items()}
    elif _type == "list":
        return [deserialize_output(v) for v in data.get("data", [])]

    # Handle resource types - return proxy classes
    if _type == "model":
        from .models import Model as ModelProxy

        return ModelProxy(data["name"])
    elif _type == "evaluation":
        from .evaluations import Eval

        return Eval(data["name"])
    elif _type == "dataset":
        from .datasets import Dataset as DatasetProxy

        return DatasetProxy(data["name"])
    elif _type == "workflow":
        from .workflows import Workflow as WorkflowProxy

        return WorkflowProxy(data["name"], run_number=data.get("run_number"))

    # Map type strings to MixType classes
    type_map = {
        "file": File,
        "image": Image,
        "video": Video,
        "audio": Audio,
        "3d": Model3D,
        "mcap": MCAP,
        "rrd": Rerun,
        "text": Text,
        "markdown": Markdown,
        "json": JSON,
        "embedding": Embedding,
    }

    if _type in type_map:
        cls = type_map[_type]
        # Extract constructor args (exclude _type)
        kwargs = {k: deserialize_output(v) for k, v in data.items() if k != "_type"}
        return cls(**kwargs)
    else:
        # Unknown type - return as dict
        return data


# =============================================================================
# Schema Extraction
# =============================================================================


def extract_output_schema(cls: type) -> dict | None:
    """Extract output schema from a class's run() method return type annotation.

    Args:
        cls: The MixFlow or MixModel class

    Returns:
        Schema dict or None if no return type annotation

    Example:
        >>> class MyModel(MixModel):
        ...     def run(self, inputs) -> dict[str, Image]:
        ...         ...
        >>> extract_output_schema(MyModel)
        {'type': 'dict', 'valueSchema': {'type': 'image'}}
    """
    # Check for explicit output_schema attribute first
    if hasattr(cls, "output_schema") and cls.output_schema is not None:
        return cls.output_schema

    # Try to extract from type hints
    if not hasattr(cls, "run"):
        return None

    try:
        hints = get_type_hints(cls.run)
        return_type = hints.get("return")
        if return_type is None:
            return None
        return _type_to_schema(return_type)
    except Exception:
        # Type hint extraction can fail for various reasons
        return None


def _type_to_schema(t: type) -> dict:
    """Convert a Python type annotation to a JSON schema dict (recursive).

    Args:
        t: A Python type (e.g., Image, list[Video], dict[str, Audio])

    Returns:
        Schema dict describing the type
    """
    # Handle None/NoneType
    if t is type(None):
        return {"type": "null"}

    # Handle Union types (e.g., Optional, Union[A, B])
    origin = get_origin(t)

    if origin is Union:
        args = get_args(t)
        # Filter out NoneType for Optional handling
        non_none_args = [a for a in args if a is not type(None)]
        if len(non_none_args) == 1:
            # Optional[X] -> just return schema for X
            return _type_to_schema(non_none_args[0])
        else:
            # Union of multiple types
            return {
                "type": "union",
                "schemas": [_type_to_schema(a) for a in non_none_args],
            }

    if origin is dict:
        args = get_args(t)
        if len(args) >= 2:
            return {"type": "dict", "valueSchema": _type_to_schema(args[1])}
        return {"type": "dict"}

    if origin is list:
        args = get_args(t)
        if args:
            return {"type": "list", "itemSchema": _type_to_schema(args[0])}
        return {"type": "list"}

    # Handle MixType subclasses (media and text types)
    type_map = {
        File: "file",
        Image: "image",
        Video: "video",
        Audio: "audio",
        Model3D: "3d",
        MCAP: "mcap",
        Rerun: "rrd",
        Text: "text",
        Markdown: "markdown",
        JSON: "json",
        Embedding: "embedding",
    }

    if t in type_map:
        return {"type": type_map[t]}

    # Handle proxy classes (lazy import to avoid circular deps)
    from .datasets import Dataset as DatasetProxy
    from .evaluations import Eval
    from .models import Model as ModelProxy
    from .workflows import Workflow as WorkflowProxy

    proxy_type_map = {
        ModelProxy: "model",
        Eval: "evaluation",
        DatasetProxy: "dataset",
        WorkflowProxy: "workflow",
    }

    if t in proxy_type_map:
        return {"type": proxy_type_map[t]}

    # Handle primitive types
    if t is str:
        return {"type": "string"}
    if t is int:
        return {"type": "integer"}
    if t is float:
        return {"type": "number"}
    if t is bool:
        return {"type": "boolean"}

    # Default for unknown types
    return {"type": "any"}


# =============================================================================
# Type aliases for convenience
# =============================================================================

# All MixType classes (media and text types only - resource types use proxy classes)
ALL_MIX_TYPES = (
    File,
    Image,
    Video,
    Audio,
    Model3D,
    MCAP,
    Rerun,
    Text,
    Markdown,
    JSON,
    Embedding,
)
