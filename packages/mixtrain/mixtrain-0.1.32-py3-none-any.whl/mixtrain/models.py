"""Model reference system for convenient model access.

This module provides a Model proxy class that makes it easy to reference
and interact with models in a workspace.

Example:
    >>> from mixtrain import get_model
    >>> model = get_model("my-model")
    >>> result = model.run({"text": "Hello world"})
    >>> print(result.video.url)  # Typed access to outputs
"""

import logging
import time
from collections.abc import Callable
from typing import Any

from .client import MixClient
from .helpers import validate_resource_name
from .result import BatchResult, ModelResult

logger = logging.getLogger(__name__)


class Model:
    """Proxy class for convenient model access and operations.

    This class wraps MixClient model operations and provides a clean,
    object-oriented interface for working with models.

    Args:
        name: Name of the model
        client: Optional MixClient instance (creates new one if not provided)

    Attributes:
        name: Model name
        client: MixClient instance for API operations

    Example:
        >>> model = Model("sentiment-analyzer")
        >>> result = model.run({"text": "Great product!"})
        >>> print(model.metadata)
        >>> print(model.runs)
    """

    def __init__(self, name: str, client: MixClient | None = None):
        """Initialize Model proxy.

        Args:
            name: Name of the model
            client: Optional MixClient instance (creates new one if not provided)

        Raises:
            ValueError: If name is invalid (must be lowercase alphanumeric with hyphens/underscores)
        """
        validate_resource_name(name, "model")
        self.name = name
        self.client = client or MixClient()
        self._metadata: dict[str, Any] | None = None
        self._runs_cache: list[dict[str, Any]] | None = None

    def submit(
        self,
        inputs: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Submit model inference asynchronously. Returns run info immediately.

        This starts a model run and returns immediately without waiting for completion.
        Use this when you want to manage the run lifecycle yourself or run multiple
        models in parallel.

        Args:
            inputs: Input data for the model (dict style)
            config: Optional configuration overrides
            **kwargs: Input data as keyword arguments (alternative to inputs dict)

        Returns:
            Run info including run_number and status

        Example:
            >>> model = Model("sentiment-analyzer")
            >>> run_info = model.submit({"text": "Great product!"})
            >>> # Or with kwargs:
            >>> run_info = model.submit(text="Great product!")
            >>> print(f"Started run #{run_info['run_number']}")
            >>> # Later, check status:
            >>> run = model.get_run(run_info['run_number'])
        """
        # Merge inputs dict with kwargs
        all_inputs = {**(inputs or {}), **kwargs}
        return self.client.run_model(
            self.name, inputs=all_inputs or None, config=config
        )

    def run(
        self,
        inputs: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
        timeout: int = 300,
        **kwargs: Any,
    ) -> ModelResult:
        """Run model inference synchronously. Blocks until completion.

        This submits a model run and polls until it completes. Use this when you
        want a simple blocking call that returns the outputs directly.

        For long-running models, uses polling with exponential backoff to avoid
        HTTP connection timeout issues.

        Args:
            inputs: Input data for the model (dict style)
            config: Optional configuration overrides
            timeout: Maximum seconds to wait for completion (default: 300)
            **kwargs: Input data as keyword arguments (alternative to inputs dict)

        Returns:
            ModelResult with typed accessors for outputs (video, image, audio, text)

        Raises:
            TimeoutError: If model doesn't complete within timeout
            ValueError: If run submission fails

        Example:
            >>> model = Model("hunyuan-video")
            >>> result = model.run({"prompt": "A cat playing piano"})
            >>> # Or with kwargs:
            >>> result = model.run(prompt="A cat playing piano")
            >>> print(result.video.url)  # Typed access
            >>> print(result.status)     # "completed"
        """
        # Merge inputs dict with kwargs
        all_inputs = {**(inputs or {}), **kwargs}

        # Submit the run
        run_info = self.submit(inputs=all_inputs or None, config=config)
        run_number = run_info.get("run_number")
        if not run_number:
            raise ValueError(f"Failed to start model run: {run_info}")

        # Poll for completion with error handling
        start_time = time.time()
        poll_interval = 0.5
        consecutive_errors = 0
        max_consecutive_errors = 5
        last_known_run: dict[str, Any] | None = None

        while time.time() - start_time < timeout:
            try:
                run = self.get_run(run_number)
                last_known_run = run
                consecutive_errors = 0  # Reset on success

                if run["status"] in ["completed", "failed", "cancelled"]:
                    return ModelResult(run, model_name=self.name)
            except Exception as e:
                consecutive_errors += 1
                logger.warning(
                    f"Failed to fetch run status (attempt {consecutive_errors}): {e}"
                )
                if consecutive_errors >= max_consecutive_errors:
                    # Return last known state or raise with context
                    if last_known_run:
                        logger.error(
                            f"Too many errors, returning last known state for run {run_number}"
                        )
                        last_known_run["_polling_error"] = str(e)
                        return ModelResult(last_known_run, model_name=self.name)
                    raise RuntimeError(
                        f"Failed to poll model run {run_number} after {max_consecutive_errors} attempts: {e}"
                    ) from e

            time.sleep(poll_interval)
            # Exponential backoff up to 5s
            poll_interval = min(poll_interval * 1.5, 5)

        raise TimeoutError(f"Model run {run_number} did not complete within {timeout}s")

    @property
    def metadata(self) -> dict[str, Any]:
        """Get model metadata (cached after first access).

        Returns:
            Model details including name, source, description, etc.

        Example:
            >>> model = Model("my-model")
            >>> print(model.metadata["source"])
            >>> print(model.metadata["description"])
        """
        if self._metadata is None:
            self._metadata = self.client.get_model(self.name)
        return self._metadata

    @property
    def spec(self) -> dict[str, Any] | None:
        """Get model specification.

        Returns:
            Model spec dictionary or None
        """
        return self.metadata.get("spec")

    @property
    def source(self) -> str:
        """Get model source (native, fal, modal, openai, anthropic, etc.).

        Returns:
            Model source string
        """
        return self.metadata.get("source", "")

    @property
    def description(self) -> str:
        """Get model description.

        Returns:
            Model description string
        """
        return self.metadata.get("description", "")

    @property
    def runs(self) -> list[dict[str, Any]]:
        """Get recent model runs (cached).

        Returns:
            List of model runs

        Example:
            >>> model = Model("my-model")
            >>> for run in model.runs:
            ...     print(f"Run #{run['run_number']}: {run['status']}")
        """
        if self._runs_cache is None:
            response = self.client.list_model_runs(self.name)
            self._runs_cache = response.get("data", [])
        return self._runs_cache

    def get_runs(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Get model runs with optional limit.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of model runs

        Example:
            >>> model = Model("my-model")
            >>> recent_runs = model.get_runs(limit=5)
        """
        response = self.client.list_model_runs(self.name)
        runs = response.get("data", [])
        if limit:
            runs = runs[:limit]
        return runs

    def get_run(self, run_number: int) -> dict[str, Any]:
        """Get details of a specific model run.

        Args:
            run_number: Run number

        Returns:
            Run details

        Example:
            >>> model = Model("my-model")
            >>> run = model.get_run(5)
            >>> print(run["status"])
        """
        return self.client.get_model_run(self.name, run_number)

    def update_run(
        self,
        run_number: int,
        status: str | None = None,
        outputs: Any | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        """Update a model run's status and outputs.

        Args:
            run_number: Run number to update
            status: New status (e.g., "running", "completed", "failed")
            outputs: Output data from the model run
            error: Error message if run failed

        Returns:
            Updated run details

        Example:
            >>> model = Model("my-model")
            >>> model.update_run(5, status="completed", outputs={"result": "success"})
        """
        return self.client.update_model_run_status(
            self.name, run_number, status=status, outputs=outputs, error=error
        )

    def cancel(self, run_number: int) -> dict[str, Any]:
        """Cancel a running model run.

        This will stop any active polling threads and attempt to cancel
        the task on the provider (FAL, Runway, Google, etc.).

        Args:
            run_number: Run number to cancel

        Returns:
            Cancelled run details

        Raises:
            ValueError: If the run cannot be cancelled (already completed/failed)

        Example:
            >>> model = Model("my-model")
            >>> run_info = model.submit({"prompt": "test"})
            >>> # Later, if you need to cancel:
            >>> model.cancel(run_info['run_number'])
        """
        return self.client.cancel_model_run(self.name, run_number)

    def get_logs(self, run_number: int | None = None) -> str:
        """Get logs for a model run.

        Args:
            run_number: Optional run number (defaults to latest run)

        Returns:
            Log content as string

        Example:
            >>> model = Model("my-model")
            >>> logs = model.get_logs()  # Latest run
            >>> print(logs)
        """
        logs_data = self.client.get_model_run_logs(self.name, run_number)
        return logs_data.get("logs", "")

    def list_files(self) -> list[dict[str, Any]]:
        """List files in the model.

        Returns:
            List of files

        Example:
            >>> model = Model("my-model")
            >>> files = model.list_files()
            >>> for file in files:
            ...     print(file["path"])
        """
        response = self.client.list_model_files(self.name)
        return response.get("data", [])

    def get_file(self, file_path: str) -> str:
        """Get content of a specific model file.

        Args:
            file_path: Path to file within model

        Returns:
            File content as string

        Example:
            >>> model = Model("my-model")
            >>> content = model.get_file("requirements.txt")
        """
        response = self.client.get_model_file(self.name, file_path)
        return response.get("content", "")

    def update(
        self, name: str | None = None, description: str | None = None
    ) -> dict[str, Any]:
        """Update model metadata.

        Args:
            name: Optional new name
            description: Optional new description

        Returns:
            Updated model data

        Example:
            >>> model = Model("my-model")
            >>> model.update(description="Updated description")
        """
        result = self.client.update_model(self.name, name=name, description=description)
        # Update local name if changed
        if name:
            self.name = name
        # Clear metadata cache
        self._metadata = None
        return result

    def delete(self) -> dict[str, Any]:
        """Delete the model.

        Returns:
            Deletion result

        Example:
            >>> model = Model("my-model")
            >>> model.delete()
        """
        return self.client.delete_model(self.name)

    @classmethod
    def exists(cls, name: str, client: MixClient | None = None) -> bool:
        """Check if a model exists.

        Args:
            name: Model name to check
            client: Optional MixClient instance

        Returns:
            True if the model exists, False otherwise

        Example:
            >>> if not Model.exists("my-model"):
            ...     Model.create("my-model", file_paths=["model.py"])
        """
        if client is None:
            client = MixClient()
        response = client.list_models()
        models = response.get("data", [])
        return any(m.get("name") == name for m in models)

    def refresh(self):
        """Clear cached data and force refresh on next access.

        Example:
            >>> model = Model("my-model")
            >>> model.refresh()
            >>> print(model.metadata)  # Will fetch fresh data
        """
        self._metadata = None
        self._runs_cache = None

    def __repr__(self) -> str:
        """String representation of the Model."""
        return f"Model(name='{self.name}', source='{self.source}')"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Model: {self.name} ({self.source})"

    @staticmethod
    def batch(
        models: list[str],
        inputs_list: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
        client: MixClient | None = None,
        max_in_flight: int = 50,
        progress_callback: Callable[[int, int], None] | None = None,
        timeout: int = 600,
        filter_failures: bool = False,
    ) -> "BatchResult":
        """Run same inputs across multiple models in parallel.

        Uses a controlled submission approach to avoid overwhelming the backend:
        1. Submit up to max_in_flight runs initially
        2. As runs complete, submit more from the queue
        3. Single polling loop checks all pending runs

        Args:
            models: List of model names to run
            inputs_list: List of input dictionaries (same for all models)
            config: Optional configuration overrides applied to all runs
            client: Optional MixClient instance
            max_in_flight: Maximum concurrent pending requests (default: 50)
            progress_callback: Optional callback(completed, total) for progress updates
            timeout: Maximum seconds to wait for all runs to complete (default: 600)
            filter_failures: If True, only include results where ALL models succeeded.

        Returns:
            BatchResult with .inputs, .to_dict(), .to_pandas() methods.

        Example:
            >>> result = Model.batch(
            ...     ["flux", "stable-diffusion"],
            ...     [{"prompt": "a cat"}, {"prompt": "a dog"}]
            ... )
            >>> df = result.to_pandas()  # Auto-converts to DataFrame

            >>> # With filter_failures to handle timeouts gracefully:
            >>> result = Model.batch(
            ...     ["flux", "stable-diffusion"],
            ...     [{"prompt": "a cat"}, {"prompt": "a dog"}],
            ...     filter_failures=True
            ... )
            >>> print(f"Succeeded: {len(result)}/{len(inputs_list)}")
            >>> df = result.to_pandas()
        """
        if client is None:
            client = MixClient()

        # Total tasks = models * inputs
        total_tasks = len(models) * len(inputs_list)
        results: dict[str, list[dict[str, Any] | None]] = {
            model: [None] * len(inputs_list) for model in models
        }

        # Build task queue: (model_name, idx, inputs)
        task_queue: list[tuple] = []
        for model_name in models:
            for idx, inputs in enumerate(inputs_list):
                task_queue.append((model_name, idx, inputs))

        # Track pending runs as (model_name, idx, run_number)
        pending_runs: list[tuple] = []
        model_instances: dict[str, Model] = {}
        task_idx = 0  # Next task to submit from queue
        completed = 0

        def submit_single(model_name: str, idx: int, inputs: dict[str, Any]) -> tuple:
            """Submit a single model run and return run info."""
            try:
                if model_name not in model_instances:
                    model_instances[model_name] = Model(model_name, client=client)
                model = model_instances[model_name]
                run_info = model.submit(inputs=inputs, config=config)
                run_number = run_info.get("run_number")
                if not run_number:
                    return (model_name, idx, None, f"Failed to start run: {run_info}")
                return (model_name, idx, run_number, None)
            except Exception as e:
                return (model_name, idx, None, str(e))

        def submit_next_task() -> bool:
            """Submit the next task from queue. Returns True if a task was submitted."""
            nonlocal task_idx, completed
            if task_idx >= len(task_queue):
                return False

            model_name, idx, inputs = task_queue[task_idx]
            task_idx += 1

            result = submit_single(model_name, idx, inputs)
            if result[3]:  # error
                logger.warning(
                    f"Model {result[0]} submission failed for input {result[1]}: {result[3]}"
                )
                results[result[0]][result[1]] = {"error": result[3], "status": "failed"}
                completed += 1
                if progress_callback:
                    progress_callback(completed, total_tasks)
                return True  # Task processed (even if failed)
            else:
                pending_runs.append((result[0], result[1], result[2]))
                return True

        # Submit initial batch up to max_in_flight
        logger.info(f"Submitting up to {max_in_flight} of {total_tasks} runs...")
        while task_idx < len(task_queue) and len(pending_runs) < max_in_flight:
            submit_next_task()

        logger.info(f"Submitted {len(pending_runs)} runs, polling for completion...")

        # Polling loop: check pending runs and submit more as slots free up
        start_time = time.time()
        poll_interval = 1.0

        if progress_callback and completed > 0:
            progress_callback(completed, total_tasks)

        while (pending_runs or task_idx < len(task_queue)) and (
            time.time() - start_time
        ) < timeout:
            still_pending = []

            for model_name, idx, run_number in pending_runs:
                try:
                    model = model_instances[model_name]
                    run = model.get_run(run_number)

                    if run["status"] in ["completed", "failed", "cancelled"]:
                        results[model_name][idx] = run
                        completed += 1
                        if progress_callback:
                            progress_callback(completed, total_tasks)

                        # Submit next task as a slot freed up
                        while (
                            task_idx < len(task_queue)
                            and len(still_pending) < max_in_flight
                        ):
                            submit_next_task()
                    else:
                        still_pending.append((model_name, idx, run_number))
                except Exception as e:
                    logger.warning(f"Error polling {model_name} run {run_number}: {e}")
                    still_pending.append((model_name, idx, run_number))

            pending_runs = still_pending

            if pending_runs or task_idx < len(task_queue):
                time.sleep(poll_interval)
                # Increase poll interval up to 5s
                poll_interval = min(poll_interval * 1.2, 5.0)

        # Handle timeouts
        for model_name, idx, run_number in pending_runs:
            results[model_name][idx] = {
                "error": f"Timeout waiting for run {run_number}",
                "status": "timeout",
                "run_number": run_number,
            }
            completed += 1
            if progress_callback:
                progress_callback(completed, total_tasks)

        # Wrap all results in ModelResult
        wrapped_results: dict[str, list[ModelResult]] = {}
        for model_name, run_list in results.items():
            wrapped_results[model_name] = [
                ModelResult(run, model_name=model_name)
                for run in run_list
                if run is not None
            ]

        # Filter failures if requested
        if filter_failures:
            from .result import RunStatus

            # Find indices where ALL models succeeded
            valid_indices = []
            for i in range(len(inputs_list)):
                all_success = all(
                    wrapped_results[model][i].status == RunStatus.COMPLETED
                    for model in models
                )
                if all_success:
                    valid_indices.append(i)

            # Log filtered count
            filtered_count = len(inputs_list) - len(valid_indices)
            if filtered_count > 0:
                logger.info(
                    f"Filtered out {filtered_count}/{len(inputs_list)} inputs due to failures"
                )

            # Filter results and inputs
            filtered_results: dict[str, list[ModelResult]] = {}
            for model_name in models:
                filtered_results[model_name] = [
                    wrapped_results[model_name][i] for i in valid_indices
                ]
            filtered_inputs = [inputs_list[i] for i in valid_indices]

            return BatchResult(inputs=filtered_inputs, _results=filtered_results)

        # Return all results (default behavior)
        return BatchResult(inputs=inputs_list, _results=wrapped_results)


def get_model(name: str, client: MixClient | None = None) -> Model:
    """Get a model reference by name.

    This is the primary way to access models in a workspace.

    Args:
        name: Model name
        client: Optional MixClient instance

    Returns:
        Model proxy instance

    Example:
        >>> from mixtrain import get_model
        >>> model = get_model("sentiment-analyzer")
        >>> result = model.run({"text": "Great!"})
    """
    return Model(name, client=client)


def list_models(
    provider: str | None = None, client: MixClient | None = None
) -> list[Model]:
    """List all models in the workspace.

    Args:
        provider: Optional filter by provider type
        client: Optional MixClient instance

    Returns:
        List of Model instances

    Example:
        >>> from mixtrain import list_models
        >>> models = list_models()
        >>> for model in models:
        ...     print(model.name)
    """
    if client is None:
        client = MixClient()

    response = client.list_models(provider=provider)
    models_data = response.get("data", [])

    return [Model(m["name"], client=client) for m in models_data]
