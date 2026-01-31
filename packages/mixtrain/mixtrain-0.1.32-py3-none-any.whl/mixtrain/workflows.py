"""Workflow reference system for convenient workflow access.

This module provides a Workflow proxy class that makes it easy to reference
and interact with workflows in a workspace.

Example:
    >>> from mixtrain import get_workflow
    >>> workflow = get_workflow("my-workflow")
    >>> print(workflow.metadata)
    >>> result = workflow.run()  # sync, blocks until complete
    >>> run_info = workflow.submit()  # async, returns immediately
"""

import logging
import time
from typing import Any

from .client import MixClient
from .helpers import validate_resource_name

logger = logging.getLogger(__name__)


class Workflow:
    """Proxy class for convenient workflow access and operations.

    This class wraps MixClient workflow operations and provides a clean,
    object-oriented interface for working with workflows.

    Usage:
        # Reference an existing workflow (lazy, no API call)
        workflow = Workflow("data-pipeline")
        result = workflow.run()  # Blocks until complete
        run_info = workflow.submit()  # Returns immediately

        # Create a new workflow
        workflow = Workflow.create("new-workflow")

    Args:
        name: Name of the workflow
        run_number: Optional specific run number (for linking to a run)
        client: Optional MixClient instance (creates new one if not provided)
        _response: Optional cached response from creation

    Attributes:
        name: Workflow name
        run_number: Optional run number
        client: MixClient instance for API operations
    """

    def __init__(
        self,
        name: str,
        run_number: int | None = None,
        client: MixClient | None = None,
        _response: dict[str, Any] | None = None,
    ):
        """Initialize Workflow proxy.

        Args:
            name: Name of the workflow
            run_number: Optional specific run number (for linking to a run)
            client: Optional MixClient instance (creates new one if not provided)
            _response: Optional cached response from creation

        Raises:
            ValueError: If name is invalid (must be lowercase alphanumeric with hyphens/underscores)
        """
        validate_resource_name(name, "workflow")
        self.name = name
        self.run_number = run_number
        self.client = client or MixClient()
        self._response = _response
        self._metadata: dict[str, Any] | None = None

    @classmethod
    def create(
        cls,
        name: str,
        description: str = "",
        client: MixClient | None = None,
    ) -> "Workflow":
        """Create a new workflow.

        Args:
            name: Name for the workflow
            description: Optional description
            client: Optional MixClient instance

        Returns:
            Workflow proxy for the created workflow

        Example:
            >>> workflow = Workflow.create("my-workflow", description="Data pipeline")
        """
        if client is None:
            client = MixClient()

        payload = {"name": name, "description": description}
        response = client._request("POST", "/workflows/", json=payload)
        return cls(name=name, client=client, _response=response.json())

    @property
    def metadata(self) -> dict[str, Any]:
        """Get workflow metadata (cached after first access).

        Returns:
            Workflow details including name, description, etc.

        Example:
            >>> workflow = Workflow("my-workflow")
            >>> print(workflow.metadata["description"])
        """
        if self._metadata is None:
            if self._response is not None:
                self._metadata = self._response
            else:
                self._metadata = self.client.get_workflow(self.name)
        return self._metadata

    @property
    def description(self) -> str:
        """Get workflow description.

        Returns:
            Workflow description string
        """
        return self.metadata.get("description", "")

    @property
    def runs(self) -> list[dict[str, Any]]:
        """Get workflow runs.

        Returns:
            List of workflow runs
        """
        return self.metadata.get("runs", [])

    def submit(self, config: dict[str, Any] | None = None) -> dict[str, Any]:
        """Submit a workflow run asynchronously. Returns run info immediately.

        This starts a workflow run and returns immediately without waiting for completion.
        Use this when you want to manage the run lifecycle yourself.

        Args:
            config: Optional configuration for the run

        Returns:
            Run info including run_number and status

        Example:
            >>> workflow = Workflow("data-pipeline")
            >>> run_info = workflow.submit({"input": "value"})
            >>> print(f"Started run #{run_info['run_number']}")
        """
        return self.client.run_workflow(self.name, json_config=config)

    def run(
        self,
        config: dict[str, Any] | None = None,
        timeout: int = 300,
    ) -> dict[str, Any]:
        """Run workflow synchronously. Blocks until completion.

        This submits a workflow run and polls until it completes. Use this when you
        want a simple blocking call that returns the outputs directly.

        Args:
            config: Optional configuration for the run
            timeout: Maximum seconds to wait for completion (default: 300)

        Returns:
            Run result including status and outputs

        Raises:
            TimeoutError: If workflow doesn't complete within timeout
            ValueError: If run submission fails

        Example:
            >>> workflow = Workflow("data-pipeline")
            >>> result = workflow.run({"input": "value"})
            >>> print(result["outputs"])
        """
        run_info = self.submit(config=config)
        run_number = run_info.get("run_number")
        if not run_number:
            raise ValueError(f"Failed to start workflow run: {run_info}")

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
                    return run
            except Exception as e:
                consecutive_errors += 1
                logger.warning(
                    f"Failed to fetch workflow run status (attempt {consecutive_errors}): {e}"
                )
                if consecutive_errors >= max_consecutive_errors:
                    # Return last known state or raise with context
                    if last_known_run:
                        logger.error(
                            f"Too many errors, returning last known state for run {run_number}"
                        )
                        last_known_run["_polling_error"] = str(e)
                        return last_known_run
                    raise RuntimeError(
                        f"Failed to poll workflow run {run_number} after {max_consecutive_errors} attempts: {e}"
                    ) from e

            time.sleep(poll_interval)
            poll_interval = min(poll_interval * 1.5, 5)

        raise TimeoutError(
            f"Workflow run {run_number} did not complete within {timeout}s"
        )

    def get_run(self, run_number: int) -> dict[str, Any]:
        """Get details of a specific workflow run.

        Args:
            run_number: Run number

        Returns:
            Run details

        Example:
            >>> workflow = Workflow("my-workflow")
            >>> run = workflow.get_run(5)
            >>> print(run["status"])
        """
        return self.client.get_workflow_run(self.name, run_number)

    def update_run(
        self,
        run_number: int,
        status: str | None = None,
        outputs: Any | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        """Update a workflow run's status and outputs.

        Args:
            run_number: Run number to update
            status: New status (e.g., "running", "completed", "failed")
            outputs: Output data from the workflow run
            error: Error message if run failed

        Returns:
            Updated run details

        Example:
            >>> workflow = Workflow("my-workflow")
            >>> workflow.update_run(5, status="completed", outputs={"result": "success"})
        """
        return self.client.update_workflow_run_status(
            self.name, run_number, status=status, outputs=outputs, error=error
        )

    def cancel(self, run_number: int) -> dict[str, Any]:
        """Cancel a running workflow run.

        Args:
            run_number: Run number to cancel

        Returns:
            Cancellation response with run details

        Raises:
            ValueError: If the run cannot be cancelled (already completed/failed)

        Example:
            >>> workflow = Workflow("my-workflow")
            >>> run_info = workflow.submit()
            >>> # Later, if you need to cancel:
            >>> workflow.cancel(run_info['run_number'])
        """
        return self.client.cancel_workflow_run(self.name, run_number)

    def delete(self) -> dict[str, Any]:
        """Delete the workflow.

        Returns:
            Deletion result

        Example:
            >>> workflow = Workflow("my-workflow")
            >>> workflow.delete()
        """
        return self.client.delete_workflow(self.name)

    def refresh(self):
        """Clear cached data and force refresh on next access.

        Example:
            >>> workflow = Workflow("my-workflow")
            >>> workflow.refresh()
            >>> print(workflow.metadata)  # Will fetch fresh data
        """
        self._metadata = None
        self._response = None

    def __repr__(self) -> str:
        """String representation of the Workflow."""
        if self.run_number:
            return f"Workflow(name='{self.name}', run_number={self.run_number})"
        return f"Workflow(name='{self.name}')"

    def __str__(self) -> str:
        """Human-readable string representation."""
        if self.run_number:
            return f"Workflow: {self.name} #{self.run_number}"
        return f"Workflow: {self.name}"


def get_workflow(name: str, client: MixClient | None = None) -> Workflow:
    """Get a workflow reference by name.

    This is the primary way to access workflows in a workspace.

    Args:
        name: Workflow name
        client: Optional MixClient instance

    Returns:
        Workflow proxy instance

    Example:
        >>> from mixtrain import get_workflow
        >>> workflow = get_workflow("data-pipeline")
        >>> result = workflow.run()  # sync
        >>> run_info = workflow.submit()  # async
    """
    return Workflow(name, client=client)


def list_workflows(client: MixClient | None = None) -> list[Workflow]:
    """List all workflows in the workspace.

    Args:
        client: Optional MixClient instance

    Returns:
        List of Workflow instances

    Example:
        >>> from mixtrain import list_workflows
        >>> workflows = list_workflows()
        >>> for wf in workflows:
        ...     print(wf.name)
    """
    if client is None:
        client = MixClient()

    response = client.list_workflows()
    workflows_data = response.get("data", [])

    return [Workflow(w["name"], client=client) for w in workflows_data]
