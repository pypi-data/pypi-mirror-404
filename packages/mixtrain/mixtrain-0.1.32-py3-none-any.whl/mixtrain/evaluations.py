"""Evaluation reference system for convenient evaluation access.

This module provides an Eval proxy class that makes it easy to reference
and interact with evaluations in a workspace.

Example:
    >>> from mixtrain import get_evaluation
    >>> eval = get_evaluation("my-eval")
    >>> print(eval.config)
    >>> eval.delete()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .client import MixClient
from .helpers import validate_resource_name

if TYPE_CHECKING:
    from .datasets import Dataset


class Eval:
    """Proxy class for convenient evaluation access and operations.

    This class wraps MixClient evaluation operations and provides a clean,
    object-oriented interface for working with evaluations.

    Usage:
        # Reference an existing evaluation (lazy, no API call)
        eval = Eval("accuracy-eval")
        print(eval.config)  # API call happens here

        # Create a new evaluation
        eval = Eval.create("new-eval", config={...})

    Args:
        name: Name of the evaluation
        client: Optional MixClient instance (creates new one if not provided)
        _response: Optional cached response from creation

    Attributes:
        name: Evaluation name
        client: MixClient instance for API operations
    """

    def __init__(
        self,
        name: str,
        client: MixClient | None = None,
        _response: dict[str, Any] | None = None,
    ):
        """Initialize Eval proxy.

        Args:
            name: Name of the evaluation
            client: Optional MixClient instance (creates new one if not provided)
            _response: Optional cached response from creation

        Raises:
            ValueError: If name is invalid (must be lowercase alphanumeric with hyphens/underscores)
        """
        validate_resource_name(name, "evaluation")
        self.name = name
        self.client = client or MixClient()
        self._response = _response
        self._metadata: dict[str, Any] | None = None

    @classmethod
    def create(
        cls,
        name: str,
        config: dict[str, Any],
        description: str = "",
        client: MixClient | None = None,
    ) -> "Eval":
        """Create a new evaluation.

        Args:
            name: Name for the evaluation
            config: Evaluation configuration
            description: Optional description
            client: Optional MixClient instance

        Returns:
            Eval proxy for the created evaluation

        Example:
            >>> eval = Eval.create("my-eval", config={"type": "comparison"})
        """
        if client is None:
            client = MixClient()

        payload = {"name": name, "description": description, "config": config}
        response = client._request("POST", "/evaluations/", json=payload)
        return cls(name=name, client=client, _response=response.json())

    @classmethod
    def from_dataset(
        cls,
        dataset: Dataset | str,
        name: str | None = None,
        description: str | None = None,
        columns: list[str] | None = None,
        client: MixClient | None = None,
    ) -> "Eval":
        """Create an evaluation from a dataset using its column types.

        Automatically builds the viz_config from the dataset's column types,
        so you don't need to manually specify the configuration.

        Args:
            dataset: Dataset instance or dataset name string
            name: Name for the evaluation (defaults to "{dataset_name}-eval")
            description: Optional description (auto-generated if not provided)
            columns: Optional list of columns to include (defaults to all typed columns)
            client: Optional MixClient instance

        Returns:
            Eval proxy for the created evaluation

        Example:
            >>> # From dataset instance
            >>> ds = Dataset("my-results")
            >>> eval = Eval.from_dataset(ds)

            >>> # From dataset name
            >>> eval = Eval.from_dataset("my-results")

            >>> # With specific columns
            >>> eval = Eval.from_dataset(ds, columns=["prompt", "image_a", "image_b"])
        """
        # Import here to avoid circular import
        from .datasets import Dataset as DatasetClass

        if client is None:
            client = MixClient()

        # Handle string dataset name
        if isinstance(dataset, str):
            dataset = DatasetClass(dataset, client=client)

        dataset_name = dataset.name

        # Get column types from dataset metadata
        column_types = dataset.column_types

        if not column_types:
            raise ValueError(
                f"Dataset '{dataset_name}' has no column types defined. "
                "Use Dataset.save() or Dataset.set_column_types() to specify types."
            )

        # Filter columns if specified
        if columns is not None:
            column_types = {k: v for k, v in column_types.items() if k in columns}
            # Preserve column order from the columns parameter
            column_types = {
                col: column_types[col] for col in columns if col in column_types
            }
            if not column_types:
                raise ValueError(
                    f"None of the specified columns {columns} have types defined "
                    f"in dataset '{dataset_name}'."
                )

        # Build viz_config from column types
        viz_config = {
            "datasets": [
                {
                    "columnName": col_name,
                    "tableName": dataset_name,
                    "dataType": col_type,
                }
                for col_name, col_type in column_types.items()
            ]
        }

        # Generate default name if not provided
        if name is None:
            name = f"{dataset_name}-eval"

        # Generate default description if not provided
        if description is None:
            type_counts = {}
            for col_type in column_types.values():
                type_counts[col_type] = type_counts.get(col_type, 0) + 1
            type_summary = ", ".join(f"{count} {t}" for t, count in type_counts.items())
            description = f"Evaluation of {dataset_name} ({type_summary})"

        return cls.create(
            name, config=viz_config, description=description, client=client
        )

    @property
    def metadata(self) -> dict[str, Any]:
        """Get evaluation metadata (cached after first access).

        Returns:
            Evaluation details including name, description, config, etc.

        Example:
            >>> eval = Eval("my-eval")
            >>> print(eval.metadata["description"])
        """
        if self._metadata is None:
            if self._response is not None:
                self._metadata = self._response
            else:
                self._metadata = self.client.get_evaluation(self.name)
        return self._metadata

    @property
    def config(self) -> dict[str, Any]:
        """Get evaluation configuration.

        Returns:
            Evaluation config dictionary
        """
        return self.metadata.get("config", {})

    @property
    def description(self) -> str:
        """Get evaluation description.

        Returns:
            Evaluation description string
        """
        return self.metadata.get("description", "")

    @property
    def status(self) -> str:
        """Get evaluation status.

        Returns:
            Evaluation status string
        """
        return self.metadata.get("status", "")

    def update(
        self,
        name: str | None = None,
        description: str | None = None,
        config: dict[str, Any] | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """Update evaluation metadata.

        Args:
            name: Optional new name
            description: Optional new description
            config: Optional new config
            status: Optional new status

        Returns:
            Updated evaluation data

        Example:
            >>> eval = Eval("my-eval")
            >>> eval.update(description="Updated description")
        """
        result = self.client.update_evaluation(
            self.name,
            name=name,
            description=description,
            config=config,
            status=status,
        )
        # Update local name if changed
        if name:
            self.name = name
        # Clear metadata cache
        self._metadata = None
        self._response = None
        return result

    def delete(self) -> dict[str, Any]:
        """Delete the evaluation.

        Returns:
            Deletion result

        Example:
            >>> eval = Eval("my-eval")
            >>> eval.delete()
        """
        return self.client.delete_evaluation(self.name)

    @classmethod
    def exists(cls, name: str, client: MixClient | None = None) -> bool:
        """Check if an evaluation exists.

        Args:
            name: Evaluation name to check
            client: Optional MixClient instance

        Returns:
            True if the evaluation exists, False otherwise

        Example:
            >>> if not Eval.exists("my-eval"):
            ...     Eval.create("my-eval", dataset="results")
        """
        if client is None:
            client = MixClient()
        response = client.list_evaluations()
        evals = response.get("data", [])
        return any(e.get("name") == name for e in evals)

    def refresh(self):
        """Clear cached data and force refresh on next access.

        Example:
            >>> eval = Eval("my-eval")
            >>> eval.refresh()
            >>> print(eval.metadata)  # Will fetch fresh data
        """
        self._metadata = None
        self._response = None

    def __repr__(self) -> str:
        """String representation of the Eval."""
        return f"Eval(name='{self.name}')"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Eval: {self.name}"


def get_eval(name: str, client: MixClient | None = None) -> Eval:
    """Get an evaluation reference by name.

    This is the primary way to access evaluations in a workspace.

    Args:
        name: Evaluation name
        client: Optional MixClient instance

    Returns:
        Eval proxy instance

    Example:
        >>> from mixtrain import get_eval
        >>> eval = get_eval("accuracy-eval")
        >>> print(eval.config)
    """
    return Eval(name, client=client)


def list_evals(client: MixClient | None = None) -> list[Eval]:
    """List all evaluations in the workspace.

    Args:
        client: Optional MixClient instance

    Returns:
        List of Eval instances

    Example:
        >>> from mixtrain import list_evals
        >>> evals = list_evals()
        >>> for e in evals:
        ...     print(e.name)
    """
    if client is None:
        client = MixClient()

    response = client.list_evaluations()
    evals_data = response.get("data", [])

    return [Eval(e["name"], client=client) for e in evals_data]
