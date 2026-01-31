"""ModelResult and BatchResult - Typed wrappers for model run results.

Provides intuitive property access to model outputs instead of complex dict navigation.

Example:
    >>> result = Model("hunyuan-video").run({"prompt": "A cat"})
    >>> result.video.url      # Instead of result["outputs"]["video"]["data"][0]["url"]
    >>> result.video.width    # Direct property access
    >>> result.status         # Run metadata

    >>> # Batch operations
    >>> batch = Model.batch(["model1", "model2"], inputs)
    >>> df = batch.to_pandas()  # Auto-converts to DataFrame
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .helpers import sanitize_model_name

# StrEnum added in Python 3.11, use (str, Enum) for 3.10 compatibility
try:
    from enum import StrEnum
except ImportError:

    class StrEnum(str, Enum):
        pass


from .types import Audio, Image, Video


class RunStatus(StrEnum):
    """Status of a model run.

    Values:
        PENDING: Run is queued, waiting to start
        RUNNING: Run is currently executing
        COMPLETED: Run finished successfully
        FAILED: Run encountered an error
        CANCELLED: Run was cancelled by user
        TIMEOUT: Run timed out (SDK-specific, from Model.batch timeout)
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ModelResult:
    """Wrapper for model run results with typed accessors.

    Provides convenient property access to outputs while maintaining
    backward compatibility with dict access.

    Attributes:
        model_name: Name of the model that produced this result (str | None)
        video: Video output (Video | None)
        image: Image output (Image | None)
        audio: Audio output (Audio | None)
        text: Text output (str | None)
        status: Run status (str)
        run_number: Run number (int | None)
        outputs: Raw outputs dict

    Example:
        >>> result = model.run({"prompt": "A cat"})
        >>> if result.video:
        ...     print(result.video.url)
        >>> # Backward compatible dict access
        >>> result["status"]  # "completed"
    """

    def __init__(self, raw: dict[str, Any], model_name: str | None = None):
        """Initialize ModelResult from raw run dict.

        Args:
            raw: Raw run result dict from API with keys like
                 "run_number", "status", "outputs", etc.
            model_name: Name of the model that produced this result.
        """
        self._raw = raw
        self._model_name = model_name
        # Handle outputs being None or missing
        self._outputs = raw.get("outputs") or {}

    @property
    def video(self) -> Video | None:
        """Extract video from outputs.

        Returns:
            Video object with url, width, height, duration_seconds,
            or None if no video output.
        """
        v = self._outputs.get("video")
        if v and isinstance(v, dict) and "url" in v:
            return Video(
                url=v.get("url", ""),
                width=v.get("width"),
                height=v.get("height"),
                duration_seconds=v.get("duration_seconds"),
                format=v.get("format"),
            )
        return None

    @property
    def image(self) -> Image | None:
        """Extract image from outputs.

        Handles both singular "image" key and plural "images" array.

        Returns:
            Image object with url, width, height,
            or None if no image output.
        """
        img = self._outputs.get("image")
        # Handle plural "images" array
        if not img:
            images = self._outputs.get("images")
            if images and isinstance(images, list) and len(images) > 0:
                img = images[0]
        if img and isinstance(img, dict) and "url" in img:
            return Image(
                url=img.get("url", ""),
                width=img.get("width"),
                height=img.get("height"),
                format=img.get("format"),
            )
        return None

    @property
    def audio(self) -> Audio | None:
        """Extract audio from outputs.

        Returns:
            Audio object with url, duration_seconds,
            or None if no audio output.
        """
        a = self._outputs.get("audio")
        if a and isinstance(a, dict) and "url" in a:
            return Audio(
                url=a.get("url", ""),
                duration_seconds=a.get("duration_seconds"),
                format=a.get("format"),
            )
        return None

    @property
    def text(self) -> str | None:
        """Extract text from various possible output keys.

        Checks keys in order: results, output, text, response, content.

        Returns:
            Text string or None if no text output.
        """
        for key in ["results", "output", "text", "response", "content"]:
            if key in self._outputs:
                val = self._outputs[key]
                # Handle primitive wrapper: {"_type": "primitive", "value": "..."}
                if isinstance(val, dict) and val.get("_type") == "primitive":
                    return val.get("value")
                return val if isinstance(val, str) else str(val)
        return None

    # Metadata accessors
    @property
    def model_name(self) -> str | None:
        """Name of the model that produced this result."""
        return self._model_name

    @property
    def status(self) -> RunStatus | str:
        """Run status (pending, running, completed, failed, cancelled, timeout).

        Returns RunStatus enum if status is a known value, otherwise returns raw string.
        Backwards compatible - string comparison works: result.status == "completed"
        """
        raw_status = self._raw.get("status", "")
        try:
            return RunStatus(raw_status)
        except ValueError:
            return raw_status  # Return raw string for unknown statuses

    @property
    def run_number(self) -> int | None:
        """Run number within the model."""
        return self._raw.get("run_number")

    @property
    def error(self) -> str | None:
        """Error message if run failed."""
        return self._raw.get("error_message") or self._raw.get("error")

    @property
    def outputs(self) -> dict[str, Any]:
        """Raw outputs dictionary for advanced access."""
        return self._outputs

    # Backward compatibility with dict access
    def __getitem__(self, key: str) -> Any:
        """Allow dict-style access: result['status']."""
        return self._raw[key]

    def __contains__(self, key: str) -> bool:
        """Allow 'in' checks: 'status' in result."""
        return key in self._raw

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-style get with default: result.get('status', 'unknown')."""
        return self._raw.get(key, default)

    def keys(self):
        """Return raw dict keys."""
        return self._raw.keys()

    def values(self):
        """Return raw dict values."""
        return self._raw.values()

    def items(self):
        """Return raw dict items."""
        return self._raw.items()

    def __repr__(self) -> str:
        """String representation."""
        if self._model_name:
            return f"ModelResult(model='{self._model_name}', status='{self.status}', run_number={self.run_number})"
        return f"ModelResult(status='{self.status}', run_number={self.run_number})"


@dataclass
class BatchResult:
    """Result of Model.batch() - batch execution across multiple models.

    Provides convenient access to batch results with conversion methods.

    Attributes:
        inputs: List of input dicts corresponding to results
        _results: Internal storage of model results

    Example:
        >>> result = Model.batch(["flux", "sdxl"], [{"prompt": "a cat"}])
        >>> df = result.to_pandas()  # Auto-detects output type
        >>> results_dict = result.to_dict()  # Get raw dict format
    """

    inputs: list[dict[str, Any]]
    _results: dict[str, list["ModelResult"]]

    def to_dict(self) -> dict[str, list["ModelResult"]]:
        """Convert to dict format: {model_name: [ModelResult, ...]}.

        Returns:
            Dict mapping model names to lists of ModelResult objects.
        """
        return self._results

    def _auto_extractor(self) -> Callable[["ModelResult"], Any]:
        """Auto-detect extractor from first successful result."""
        for model_results in self._results.values():
            for r in model_results:
                if r.image:
                    return lambda r: r.image.url if r.image else None
                elif r.video:
                    return lambda r: r.video.url if r.video else None
                elif r.audio:
                    return lambda r: r.audio.url if r.audio else None
                elif r.text is not None:
                    return lambda r: r.text
        return lambda r: str(r) if r else None

    def to_pandas(self, extractor: Callable[["ModelResult"], Any] | None = None):
        """Convert to pandas DataFrame.

        Automatically includes all input keys as columns and auto-detects
        the output type (image/video/audio/text) for model result columns.

        Args:
            extractor: Optional function to extract value from ModelResult.
                      If not provided, auto-detects based on output type.

        Returns:
            DataFrame with input columns + model result columns.

        Example:
            >>> result = Model.batch(["flux", "sdxl"], inputs)
            >>> df = result.to_pandas()  # Auto-detect
            >>> df = result.to_pandas(lambda r: r.text)  # Custom extractor
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required for to_pandas()")

        if extractor is None:
            extractor = self._auto_extractor()

        # All input keys become columns automatically
        df = pd.DataFrame(self.inputs)

        # Add model result columns
        for model, model_results in self._results.items():
            df[sanitize_model_name(model)] = [extractor(r) for r in model_results]

        return df

    def __len__(self) -> int:
        """Return number of results."""
        return len(self.inputs)

    def __repr__(self) -> str:
        """String representation."""
        models = list(self._results.keys())
        return f"BatchResult(models={models}, count={len(self)})"
