"""MixClient - Client for Mixtrain SDK

This module provides the core MixClient class that handles authentication,
workspace management, and all API operations for the Mixtrain platform.
"""

import functools
import inspect
import json
import os
from collections.abc import Generator
from enum import Enum
from functools import lru_cache
from logging import getLogger
from typing import Any

import httpx
from pyiceberg.catalog import load_catalog
from pyiceberg.table import Table

from .types import serialize_output
from .utils import auth as auth_utils
from .utils.config import get_config

logger = getLogger(__name__)


class AuthMethod(Enum):
    """Authentication methods supported by MixClient."""

    API_KEY = "api_key"
    LOGIN_TOKEN = "login_token"


class MixClient:
    """Main client for interacting with the Mixtrain platform.

    Handles authentication, workspace management, and all API operations.

    Usage:
        # Auto-detect authentication and workspace
        client = MixClient()

        # API key authentication - scoped to the key's workspace and role
        client = MixClient(api_key="mix-abc123")

        # Login token with specific workspace
        client = MixClient(workspace_name="my-workspace")

    Note:
        API keys authenticate to a specific workspace with a specific role (ADMIN/MEMBER/VIEWER).
        Each API key can only access its assigned workspace and cannot perform user-specific
        operations like managing invitations or creating new workspaces.

        The workspace_name parameter is automatically determined from the API key and should
        not be manually specified when using API key authentication.
    """

    def __init__(self, workspace_name: str | None = None, api_key: str | None = None):
        """Initialize MixClient.

        Args:
            workspace_name: Workspace to use (only for login token auth).
                          For API keys, workspace is auto-determined.
            api_key: API key for authentication. If not provided, will check environment
                    or fall back to login token.
        """
        self._explicit_workspace = workspace_name
        self._explicit_api_key = api_key
        self._auth_method = self._detect_auth_method()

        # Validate that workspace_name is not provided with API key
        if self._auth_method == AuthMethod.API_KEY and workspace_name:
            raise ValueError(
                "workspace_name should not be specified when using API key authentication. "
                "The workspace is automatically determined from the API key."
            )

        self._workspace_name = self._determine_workspace_name()

    def _detect_auth_method(self) -> AuthMethod:
        """Detect which authentication method to use."""
        # Priority: explicit API key > env API key > login token
        if self._explicit_api_key:
            if not self._explicit_api_key.startswith("mix-"):
                raise ValueError("API key must start with 'mix-'")
            return AuthMethod.API_KEY

        env_api_key = os.getenv("MIXTRAIN_API_KEY")
        if env_api_key:
            if not env_api_key.startswith("mix-"):
                raise ValueError(
                    "MIXTRAIN_API_KEY environment variable must start with 'mix-'"
                )
            return AuthMethod.API_KEY

        # Check if we have a login token
        config = get_config()
        if config.get_auth_token():
            return AuthMethod.LOGIN_TOKEN

        raise ValueError(
            "No authentication method available. "
            "Please set MIXTRAIN_API_KEY environment variable or authenticate with 'mixtrain login'"
        )

    def _determine_workspace_name(self) -> str:
        """Determine which workspace to use."""
        if self._explicit_workspace:
            return self._explicit_workspace

        if self._auth_method == AuthMethod.API_KEY:
            # For API key auth, the key is workspace-specific, so we can determine the workspace
            # from the key itself by calling the workspaces endpoint. Since the API key belongs to
            # a specific workspace, it will only have access to that workspace.
            workspaces = self.list_workspaces()
            workspace_list = workspaces.get("data", [])
            if not workspace_list:
                raise ValueError("No workspaces available with current API key")

            # Since API keys are workspace-specific, there should typically be only one workspace
            # If there are multiple, use the first one (the key has access to it)
            return workspace_list[0]["name"]

        else:  # LOGIN_TOKEN
            # For login token, use configured active workspace
            config = get_config()
            active_workspace = next((w for w in config.workspaces if w.active), None)
            if not active_workspace:
                raise ValueError(
                    "No active workspace found. Please authenticate with 'mixtrain login'"
                )
            return active_workspace.name

    def _get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for API requests."""
        if self._auth_method == AuthMethod.API_KEY:
            api_key = self._explicit_api_key or os.getenv("MIXTRAIN_API_KEY")
            return {"X-API-Key": api_key}
        else:  # LOGIN_TOKEN
            config = get_config()
            auth_token = config.get_auth_token()
            if not auth_token:
                raise ValueError("No auth token available")
            return {"Authorization": f"Bearer {auth_token}"}

    def _get_platform_url(self) -> str:
        """Get platform URL with environment variable override."""
        return os.getenv("MIXTRAIN_PLATFORM_URL", "https://platform.mixtrain.ai/api/v1")

    def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        file_paths: list[str] | None = None,
        file_base_dir: str | None = None,
        form_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        workspace_scoped: bool = True,
    ) -> httpx.Response:
        """Make HTTP request to the platform API.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (auto-prefixed with workspace path unless workspace_scoped=False)
            json: JSON payload (sent as JSON body)
            file_paths: List of file paths to upload (uploaded under "files" field)
            file_base_dir: Base directory for computing relative paths (if None, uses commonpath)
            form_data: Form fields to send as multipart (use instead of json for multipart-only endpoints)
            params: Query parameters
            workspace_scoped: If True, prepend /workspaces/{workspace_name} to path

        Returns:
            HTTP response object

        Raises:
            Exception: On HTTP errors or connection issues
        """
        if workspace_scoped:
            path = f"/workspaces/{self._workspace_name}{path}"

        url = f"{self._get_platform_url()}{path}"

        file_handles = []
        try:
            kwargs: dict[str, Any] = {
                "params": params,
                "headers": self._get_auth_headers(),
            }

            if file_paths or form_data is not None:
                # Multipart mode: send files and/or form fields
                files_list = []

                if file_paths:
                    abs_paths = [os.path.abspath(fp) for fp in file_paths]

                    # Use provided base_dir or compute from common path
                    if file_base_dir:
                        base_dir = os.path.abspath(file_base_dir)
                    else:
                        # Compute relative paths from common base directory
                        base_dir = os.path.commonpath(abs_paths)
                        # If base_dir is a file, use its parent directory
                        if os.path.isfile(base_dir):
                            base_dir = os.path.dirname(base_dir)

                    for fp in file_paths:
                        file_handles.append(open(fp, "rb"))

                    # Use relative path from base to preserve directory structure
                    rel_paths = [os.path.relpath(fp, base_dir) for fp in abs_paths]
                    files_list = [
                        ("files", (rel_path, h, "application/octet-stream"))
                        for rel_path, h in zip(rel_paths, file_handles, strict=False)
                    ]

                # Add form fields as multipart entries
                if form_data:
                    for key, value in form_data.items():
                        if value is None:
                            continue
                        if isinstance(value, list):
                            for v in value:
                                files_list.append((key, (None, str(v))))
                        else:
                            files_list.append((key, (None, str(value))))

                kwargs["files"] = files_list
            elif json is not None:
                kwargs["json"] = json

            with httpx.Client(timeout=30.0) as client:
                response = client.request(method, url, **kwargs)

            if not response.is_success:
                try:
                    error_detail = response.json().get("detail", response.text)
                except Exception:
                    error_detail = response.text
                raise Exception(
                    error_detail or f"Request failed with status {response.status_code}"
                )

            return response

        except httpx.RequestError as exc:
            raise Exception(f"Network error: {exc}")
        finally:
            for handle in file_handles:
                handle.close()

    @property
    def workspace_name(self) -> str:
        """Get current workspace name."""
        return self._workspace_name

    def frontend_url(self, path: str) -> str:
        """Get frontend URL for a resource path.

        Args:
            path: Resource path (e.g., "/models/my-model")

        Returns:
            Full frontend URL with workspace prefix
        """
        base = os.getenv("FRONTEND_URL", "https://app.mixtrain.ai")
        return f"{base}/{self._workspace_name}{path}"

    @property
    def auth_method(self) -> AuthMethod:
        """Get current authentication method."""
        return self._auth_method

    def model(self, name: str):
        """Get a Model proxy for convenient access.

        Args:
            name: Model name

        Returns:
            Model proxy instance

        Example:
            >>> client = MixClient()
            >>> model = client.model("my-model")
            >>> result = model.run({"text": "Hello"})
        """
        # Late import to avoid circular dependency
        from .models import Model

        return Model(name, client=self)

    def router(self, name: str):
        """Get a Router proxy for convenient access.

        Args:
            name: Router name

        Returns:
            Router proxy instance

        Example:
            >>> client = MixClient()
            >>> router = client.router("my-router")
            >>> result = router.route({"user": {"tier": "premium"}})
        """
        # Late import to avoid circular dependency
        from .routers import Router

        return Router(name, client=self)

    # Workspace operations
    def list_workspaces(self) -> dict[str, Any]:
        """List all workspaces the user has access to."""
        response = self._request("GET", "/workspaces/list", workspace_scoped=False)
        return response.json()

    def create_workspace(self, name: str, description: str = "") -> dict[str, Any]:
        """Create a new workspace."""
        response = self._request(
            "POST",
            "/workspaces/",
            json={"name": name, "description": description},
            workspace_scoped=False,
        )
        return response.json()

    def delete_workspace(self, workspace_name: str) -> None:
        """Delete a workspace."""
        self._request("DELETE", f"/workspaces/{workspace_name}", workspace_scoped=False)

    # Dataset operations
    def list_datasets(self) -> dict[str, Any]:
        """List all datasets in the current workspace."""
        response = self._request(
            "GET",
            f"/lakehouse/workspaces/{self._workspace_name}/tables",
            workspace_scoped=False,
        )
        return response.json()

    # Evaluation operations
    def list_evaluations(self) -> dict[str, Any]:
        """List all evaluations in the current workspace."""
        response = self._request("GET", "/evaluations/")
        return response.json()

    def get_evaluation(self, evaluation_name: str) -> dict[str, Any]:
        """Get a specific evaluation by name.

        Note: Prefer using Eval(name) for a cleaner API that returns an Eval proxy.

        Args:
            evaluation_name: Name of the evaluation (slug format: lowercase, hyphens only)

        Returns:
            Evaluation data dict
        """
        # evaluation_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        response = self._request("GET", f"/evaluations/{evaluation_name}")
        return response.json()

    def update_evaluation(
        self,
        evaluation_name: str,
        name: str | None = None,
        description: str | None = None,
        config: dict[str, Any] | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """Update fields on an evaluation.

        Args:
            evaluation_name: Current name of the evaluation
            name: Optional new name for the evaluation
            description: Optional new description
            config: Optional new config
            status: Optional new status

        Returns:
            Updated evaluation data
        """
        # evaluation_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if config is not None:
            payload["config"] = config
        if status is not None:
            payload["status"] = status
        response = self._request(
            "PATCH",
            f"/evaluations/{evaluation_name}",
            json=payload,
        )
        return response.json()

    def delete_evaluation(self, evaluation_name: str) -> None:
        """Delete an evaluation by name.

        Args:
            evaluation_name: Name of the evaluation to delete
        """
        # evaluation_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        self._request("DELETE", f"/evaluations/{evaluation_name}")

    def get_evaluation_data(
        self,
        datasets: list[dict[str, Any]],
        evaluation_name: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Fetch evaluation data for side-by-side comparison across datasets.

        Args:
            datasets: List of dataset configs with keys: tableName, columnName, dataType.
            evaluation_name: Optional evaluation name for caching.
            limit: Page size.
            offset: Offset for pagination.
        """
        payload: dict[str, Any] = {
            "datasets": datasets,
            "limit": limit,
            "offset": offset,
        }
        if evaluation_name is not None:
            payload["evaluationName"] = evaluation_name
        response = self._request(
            "POST",
            f"/lakehouse/workspaces/{self._workspace_name}/evaluation/data",
            json=payload,
            workspace_scoped=False,
        )
        return response.json()

    def delete_dataset(self, name: str) -> httpx.Response:
        """Delete a dataset."""
        return self._request(
            "DELETE",
            f"/lakehouse/workspaces/{self._workspace_name}/tables/{name}",
            workspace_scoped=False,
        )

    @lru_cache(maxsize=1)
    def get_catalog(self) -> Any:
        """Get PyIceberg catalog for the workspace."""
        try:
            provider_secrets = self._request(
                "GET",
                "/dataset-providers/type/apache_iceberg",
            ).json()

            if provider_secrets["provider_type"] != "apache_iceberg":
                raise Exception(
                    f"Dataset provider {provider_secrets['provider_type']} is not supported"
                )

            warehouse_uri = provider_secrets["secrets"]["CATALOG_WAREHOUSE_URI"]

            # Handle GCS warehouse credentials
            if (
                os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") is None
                and warehouse_uri.startswith("gs://")
                and provider_secrets["secrets"].get("SERVICE_ACCOUNT_JSON")
            ):
                service_account_json = provider_secrets["secrets"][
                    "SERVICE_ACCOUNT_JSON"
                ]
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
                    f"/tmp/{self._workspace_name}/service_account.json"
                )

                # Set up Google Cloud credentials (temporary file)
                os.makedirs(f"/tmp/mixtrain/{self._workspace_name}", exist_ok=True)
                with open(
                    f"/tmp/mixtrain/{self._workspace_name}/service_account.json", "w"
                ) as f:
                    f.write(service_account_json)

                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
                    f"/tmp/mixtrain/{self._workspace_name}/service_account.json"
                )

            # Load the catalog
            catalog_config = {
                "type": provider_secrets["secrets"]["CATALOG_TYPE"],
                "uri": provider_secrets["secrets"]["CATALOG_URI"],
                "warehouse": warehouse_uri,
                "pool_pre_ping": "true",
                "pool_recycle": "3600",
                "pool_size": "5",
                "max_overflow": "10",
                "pool_timeout": "30",
            }

            # Handle S3 warehouse credentials
            if warehouse_uri.startswith("s3://"):
                aws_access_key = provider_secrets["secrets"].get("AWS_ACCESS_KEY_ID")
                aws_secret_key = provider_secrets["secrets"].get(
                    "AWS_SECRET_ACCESS_KEY"
                )
                s3_endpoint = provider_secrets["secrets"].get("S3_ENDPOINT_URL")

                if aws_access_key and aws_secret_key:
                    catalog_config["s3.access-key-id"] = aws_access_key
                    catalog_config["s3.secret-access-key"] = aws_secret_key
                    if s3_endpoint:
                        catalog_config["s3.endpoint"] = s3_endpoint
                        catalog_config["s3.path-style-access"] = "true"

            catalog = load_catalog("default", **catalog_config)
            return catalog

        except Exception as e:
            raise Exception(f"Failed to load catalog: {e}")

    def get_dataset(self, name: str) -> Table:
        """Get an Iceberg table using workspace secrets and PyIceberg catalog API.

        Note: Prefer using Dataset(name) for a cleaner API that returns a Dataset proxy.

        Args:
            name: Dataset name

        Returns:
            PyIceberg Table
        """
        catalog = self.get_catalog()
        table_identifier = f"{self._workspace_name}.{name}"
        table = catalog.load_table(table_identifier)
        return table

    def get_dataset_metadata(self, name: str) -> dict[str, Any]:
        """Get detailed metadata for a table.

        Args:
            name: Dataset name

        Returns:
            Dataset metadata dict
        """
        # Get metadata from list and filter by name
        response = self.list_datasets()
        datasets = response.get("data", [])
        for ds in datasets:
            if ds.get("name") == name:
                return ds
        return {"name": name}

    def get_dataset_detailed_metadata(self, name: str) -> dict[str, Any]:
        """Get detailed metadata for a dataset including column types.

        Args:
            name: Dataset name

        Returns:
            Detailed dataset metadata dict including schema, column_types, etc.
        """
        response = self._request(
            "GET",
            f"/lakehouse/workspaces/{self._workspace_name}/tables/{name}/metadata?provider_type=apache_iceberg",
            workspace_scoped=False,
        )
        return response.json()

    def update_dataset_metadata(
        self,
        name: str,
        description: str | None = None,
        column_types: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Update dataset metadata (description, column_types).

        Args:
            name: Dataset name
            description: Optional new description for the dataset
            column_types: Optional dict mapping column names to display types.
                         Valid types: image, video, audio, text, 3d

        Returns:
            API response dict with updated metadata

        Example:
            >>> client.update_dataset_metadata("my-dataset", column_types={
            ...     "image_url": "image",
            ...     "video_url": "video",
            ...     "description": "text"
            ... })
        """
        payload: dict[str, Any] = {}
        if description is not None:
            payload["description"] = description
        if column_types is not None:
            payload["column_types"] = column_types

        if not payload:
            raise ValueError(
                "At least one of description or column_types must be provided"
            )

        response = self._request(
            "PATCH",
            f"/lakehouse/workspaces/{self._workspace_name}/tables/{name}/metadata?provider_type=apache_iceberg",
            json=payload,
            workspace_scoped=False,
        )
        return response.json()

    # Dataset provider operations
    def list_dataset_providers(self) -> dict[str, Any]:
        """List available and onboarded dataset providers."""
        response = self._request("GET", "/dataset-providers/")
        return response.json()

    def create_dataset_provider(
        self, provider_type: str, secrets: dict[str, str]
    ) -> dict[str, Any]:
        """Onboard a new dataset provider for the workspace."""
        payload = {"provider_type": provider_type, "secrets": secrets}
        response = self._request(
            "POST",
            "/dataset-providers/",
            json=payload,
        )
        return response.json()

    def update_dataset_provider(
        self, provider_uuid: str, secrets: dict[str, str]
    ) -> dict[str, Any]:
        """Update secrets for an existing dataset provider."""
        payload = {"secrets": secrets}
        response = self._request(
            "PUT",
            f"/dataset-providers/{provider_uuid}",
            json=payload,
        )
        return response.json()

    def delete_dataset_provider(self, provider_uuid: str) -> None:
        """Remove a dataset provider from the workspace."""
        self._request(
            "DELETE",
            f"/dataset-providers/{provider_uuid}",
        )
        # 204 No Content indicates success

    # Model provider operations
    def list_model_providers(self) -> dict[str, Any]:
        """List available and onboarded model providers."""
        response = self._request("GET", "/models/providers")
        return response.json()

    def create_model_provider(
        self, provider_type: str, secrets: dict[str, str]
    ) -> dict[str, Any]:
        """Onboard a new model provider for the workspace."""
        payload = {"provider_type": provider_type, "secrets": secrets}
        response = self._request("POST", "/models/providers", json=payload)
        return response.json()

    def update_model_provider(
        self, provider_uuid: str, secrets: dict[str, str]
    ) -> dict[str, Any]:
        """Update secrets for an existing model provider."""
        payload = {"secrets": secrets}
        response = self._request(
            "PUT",
            f"/models/providers/{provider_uuid}",
            json=payload,
        )
        return response.json()

    def delete_model_provider(self, provider_uuid: str) -> None:
        """Remove a model provider from the workspace."""
        self._request(
            "DELETE",
            f"/models/providers/{provider_uuid}",
        )
        # 204 No Content indicates success

    # Secret operations
    def get_secret(self, secret_name: str) -> str:
        """Get a secret value by name.

        Args:
            secret_name: Name of the secret to retrieve

        Returns:
            The decoded secret value as a string

        Raises:
            Exception: If secret is not found or there's an API error
        """
        response = self._request("GET", f"/secrets/{secret_name}")
        secret_data = response.json()
        return secret_data.get("value", "")

    def get_all_secrets(self) -> dict[str, Any]:
        """Get all secrets in the current workspace."""
        response = self._request("GET", "/secrets/")
        return response.json()

    def list_models(self, provider: str | None = None) -> dict[str, Any]:
        """List models in the current workspace.

        Args:
            provider: Optional filter by model type - "native", "provider", or None for all

        Returns:
            Dict with 'data' key containing list of models
        """
        params = {"provider": provider} if provider else None
        response = self._request("GET", "/models/", params=params)
        return response.json()

    def get_catalog_models(self, provider: str | None = None) -> dict[str, Any]:
        """Browse provider model catalog.

        Args:
            provider: Optional filter by provider name

        Returns:
            Dict with available provider models
        """
        params = {"provider": provider} if provider else None
        response = self._request("GET", "/models/catalog", params=params)
        return response.json()

    def get_model(self, model_name: str) -> dict[str, Any]:
        """Get model details.

        Args:
            model_name: Name of the model

        Returns:
            Model details
        """
        response = self._request("GET", f"/models/{model_name}")
        return response.json()

    def create_model(
        self,
        name: str,
        file_paths: list[str],
        description: str = "",
    ) -> dict[str, Any]:
        """Create a native model from local files.

        Args:
            name: Model name
            file_paths: List of file paths to upload
            description: Model description

        Returns:
            Created model data
        """
        response = self._request(
            "POST",
            "/models/",
            file_paths=file_paths,
            form_data={"name": name, "description": description},
        )
        return response.json()

    def register_model(
        self,
        name: str,
        provider: str,
        provider_model_id: str,
        description: str = "",
    ) -> dict[str, Any]:
        """Register a provider model.

        Args:
            name: Model name in workspace
            provider: Provider name (e.g., "openai", "anthropic")
            provider_model_id: Model ID from provider
            description: Model description

        Returns:
            Registered model data
        """
        payload = {
            "name": name,
            "provider": provider,
            "provider_model_id": provider_model_id,
            "description": description,
        }
        response = self._request(
            "POST",
            "/models/register",
            json=payload,
        )
        return response.json()

    def update_model(
        self,
        model_name: str,
        name: str | None = None,
        description: str | None = None,
        file_paths: list[str] | None = None,
        file_base_dir: str | None = None,
        delete_files: list[str] | None = None,
    ) -> dict[str, Any]:
        """Update model metadata and/or files.

        Args:
            model_name: Current model name
            name: Optional new name
            description: Optional new description
            file_paths: Optional list of file paths to upload
            file_base_dir: Base directory for computing relative paths when uploading
            delete_files: Optional list of file paths to delete from the model

        Returns:
            Updated model data
        """
        form_data: dict[str, Any] = {}
        if name is not None:
            form_data["display_name"] = name
        if description is not None:
            form_data["description"] = description
        if delete_files is not None:
            form_data["delete_files"] = delete_files

        response = self._request(
            "PATCH",
            f"/models/{model_name}",
            file_paths=file_paths,
            file_base_dir=file_base_dir,
            form_data=form_data,
        )
        return response.json()

    def delete_model(self, model_name: str) -> None:
        """Delete a model.

        Args:
            model_name: Name of the model to delete
        """
        self._request("DELETE", f"/models/{model_name}")

    def list_model_files(self, model_name: str) -> dict[str, Any]:
        """List files in a model.

        Args:
            model_name: Name of the model

        Returns:
            List of files
        """
        response = self._request("GET", f"/models/{model_name}/files")
        return response.json()

    def get_model_file(self, model_name: str, file_path: str) -> dict[str, Any]:
        """Get content of a specific model file.

        Args:
            model_name: Name of the model
            file_path: Path to file within model

        Returns:
            File content
        """
        response = self._request(
            "GET",
            f"/models/{model_name}/files/{file_path}",
        )
        return response.json()

    def delete_model_file(self, model_name: str, file_path: str) -> dict[str, Any]:
        """Delete a specific file from a model.

        Args:
            model_name: Name of the model
            file_path: Path to file within model

        Returns:
            Updated model data
        """
        return self.update_model(model_name, delete_files=[file_path])

    def run_model(
        self,
        model_name: str,
        inputs: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
        sandbox: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run model inference.

        Args:
            model_name: Name of the model
            inputs: Input data for the model
            config: Optional configuration overrides
            sandbox: Optional sandbox configuration (GPU, memory, etc.)

        Returns:
            Run result with outputs
        """
        payload_config = config or {}
        if sandbox:
            payload_config["sandbox"] = sandbox

        payload = {
            "inputs": inputs or {},
            "config": payload_config,
        }
        response = self._request(
            "POST",
            f"/models/{model_name}/run",
            json=payload,
        )
        return response.json()

    def list_model_runs(
        self, model_name: str, limit: int = 50, offset: int = 0
    ) -> dict[str, Any]:
        """List runs for a model with pagination.

        Args:
            model_name: Name of the model
            limit: Maximum number of runs to return (default 50)
            offset: Number of runs to skip (default 0)

        Returns:
            Dict with runs list, total count, and pagination info
        """
        response = self._request(
            "GET",
            f"/models/{model_name}/runs",
            params={"limit": limit, "offset": offset},
        )
        return response.json()

    def get_model_run(self, model_name: str, run_number: int) -> dict[str, Any]:
        """Get details of a specific model run.

        Args:
            model_name: Name of the model
            run_number: Run number

        Returns:
            Run details
        """
        response = self._request(
            "GET",
            f"/models/{model_name}/runs/{run_number}",
        )
        return response.json()

    def update_model_run_status(
        self,
        model_name: str,
        run_number: int,
        status: str,
        outputs: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        """Update model run status.

        Args:
            model_name: Name of the model
            run_number: Run number
            status: New status (pending, running, completed, failed)
            outputs: Optional run outputs
            error: Optional error message

        Returns:
            Updated run data
        """
        payload = {"status": status}
        if outputs is not None:
            payload["outputs"] = serialize_output(outputs)
        if error is not None:
            payload["error"] = error

        response = self._request(
            "PATCH",
            f"/models/{model_name}/runs/{run_number}",
            json=payload,
        )
        return response.json()

    def cancel_model_run(self, model_name: str, run_number: int) -> dict[str, Any]:
        """Cancel a running model run.

        This will stop any active polling threads and attempt to cancel
        the task on the provider (FAL, Runway, Google, etc.).

        Args:
            model_name: Name of the model
            run_number: Run number to cancel

        Returns:
            Cancelled run details
        """
        return self.update_model_run_status(model_name, run_number, status="cancelled")

    def get_model_run_logs(self, model_name: str, run_number: int) -> str:
        """Get logs for a model run.

        Args:
            model_name: Name of the model
            run_number: Run number

        Returns:
            Log text (plain text, not JSON)
        """
        path = f"/models/{model_name}/runs/{run_number}/logs?output_format=text"
        response = self._request("GET", path)
        return response.text

    # Workflow operations
    def list_workflows(self) -> dict[str, Any]:
        """List all workflows in the workspace."""
        response = self._request("GET", "/workflows/")
        return response.json()

    def create_workflow(
        self,
        name: str,
        file_paths: list[str],
        description: str = "",
    ) -> dict[str, Any]:
        """Create a new workflow with file uploads.

        Args:
            name: Workflow name
            file_paths: List of file paths to upload
            description: Workflow description

        Returns:
            Created workflow data
        """
        response = self._request(
            "POST",
            "/workflows/",
            file_paths=file_paths,
            form_data={"name": name, "description": description},
        )
        return response.json()

    def get_workflow(self, workflow_name: str) -> dict[str, Any]:
        """Get a specific workflow with its runs.

        Args:
            workflow_name: Name of the workflow (slug format: lowercase, hyphens only)

        Returns:
            Workflow data with runs
        """
        # workflow_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        response = self._request("GET", f"/workflows/{workflow_name}")
        return response.json()

    def update_workflow(
        self,
        workflow_name: str,
        name: str | None = None,
        description: str | None = None,
        file_paths: list[str] | None = None,
        file_base_dir: str | None = None,
        delete_files: list[str] | None = None,
    ) -> dict[str, Any]:
        """Update a workflow.

        Args:
            workflow_name: Current name of the workflow
            name: Optional new name for the workflow
            description: Optional new description
            file_paths: Optional list of file paths to upload
            file_base_dir: Base directory for computing relative paths when uploading
            delete_files: Optional list of file paths to delete from the workflow

        Returns:
            Updated workflow data
        """
        form_data: dict[str, Any] = {}
        if name is not None:
            form_data["name"] = name
        if description is not None:
            form_data["description"] = description
        if delete_files is not None:
            form_data["delete_files"] = delete_files

        response = self._request(
            "PATCH",
            f"/workflows/{workflow_name}",
            file_paths=file_paths,
            file_base_dir=file_base_dir,
            form_data=form_data,
        )
        return response.json()

    def delete_workflow(self, workflow_name: str) -> None:
        """Delete a workflow.

        Args:
            workflow_name: Name of the workflow to delete
        """
        # workflow_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        self._request("DELETE", f"/workflows/{workflow_name}")

    def list_workflow_runs(
        self, workflow_name: str, limit: int = 50, offset: int = 0
    ) -> dict[str, Any]:
        """List runs for a workflow with pagination.

        Args:
            workflow_name: Name of the workflow
            limit: Maximum number of runs to return (default 50)
            offset: Number of runs to skip (default 0)

        Returns:
            Dict with runs list, total count, and pagination info
        """
        # workflow_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        response = self._request(
            "GET",
            f"/workflows/{workflow_name}/runs",
            params={"limit": limit, "offset": offset},
        )
        return response.json()

    def start_workflow_run(
        self,
        workflow_name: str,
        json_config: dict[str, Any] | str | None = None,
    ) -> dict[str, Any]:
        """Start a new workflow run with optional configuration overrides.

        Args:
            workflow_name: Name of the workflow to run
            json_config: Optional configuration to override workflow defaults.
                        Can be a dictionary, a JSON string, or a path to a JSON file.

        Returns:
            Workflow run data
        """
        # Handle json_config if it's a string (file path or JSON string)
        config_dict = {}
        if json_config:
            if isinstance(json_config, str):
                if os.path.exists(json_config):
                    with open(json_config) as f:
                        config_dict = json.load(f)
                else:
                    try:
                        config_dict = json.loads(json_config)
                    except json.JSONDecodeError:
                        # If it's not a valid JSON string and not a file, raise error
                        raise ValueError(
                            "json_config must be a valid JSON string or an existing file path"
                        )
            else:
                config_dict = json_config

        # workflow_name is slug-validated (^[a-z][a-z0-9_-]{0,62}$), encoding not needed
        payload = {"json_config": config_dict}
        response = self._request(
            "POST",
            f"/workflows/{workflow_name}/runs",
            json=payload,
        )
        return response.json()

    def get_workflow_run(self, workflow_name: str, run_number: int) -> dict[str, Any]:
        """Get a specific workflow run.

        Args:
            workflow_name: Name of the workflow
            run_number: Per-workflow run number (1, 2, 3...)

        Returns:
            Workflow run data
        """
        # workflow_name is slug-validated (^[a-z][a-z0-9-]{0,62}$), encoding not needed
        response = self._request(
            "GET",
            f"/workflows/{workflow_name}/runs/{run_number}",
        )
        return response.json()

    def update_workflow_run_status(
        self,
        workflow_name: str,
        run_number: int,
        status: str | None = None,
        json_config: dict[str, Any] | None = None,
        logs_url: str | None = None,
        outputs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update a workflow run status and other fields.

        Args:
            workflow_name: Name of the workflow
            run_number: Per-workflow run number
            status: Optional new status. Valid values: 'pending', 'running', 'completed', 'failed', 'cancelled'
            json_config: Optional configuration to override
            logs_url: Optional URL to the run logs
            outputs: Optional typed outputs from the workflow run

        Returns:
            Updated workflow run data
        """
        # workflow_name is slug-validated (^[a-z][a-z0-9-]{0,62}$), encoding not needed
        payload = {}
        if status is not None:
            payload["status"] = status
        if json_config is not None:
            payload["json_config"] = json_config
        if logs_url is not None:
            payload["logs_url"] = logs_url
        if outputs is not None:
            payload["outputs"] = serialize_output(outputs)

        response = self._request(
            "PATCH",
            f"/workflows/{workflow_name}/runs/{run_number}",
            json=payload,
        )
        return response.json()

    def cancel_workflow_run(
        self, workflow_name: str, run_number: int
    ) -> dict[str, Any]:
        """Cancel a running workflow.

        Args:
            workflow_name: Name of the workflow
            run_number: Per-workflow run number to cancel

        Returns:
            Cancellation result
        """
        # workflow_name is slug-validated (^[a-z][a-z0-9-]{0,62}$), encoding not needed
        response = self._request(
            "POST",
            f"/workflows/{workflow_name}/runs/{run_number}/cancel",
            json={},
        )
        return response.json()

    def get_workflow_run_logs(self, workflow_name: str, run_number: int) -> str:
        """Get logs for a workflow run.

        Args:
            workflow_name: Name of the workflow
            run_number: Run number

        Returns:
            Log text (plain text, not JSON)
        """
        path = f"/workflows/{workflow_name}/runs/{run_number}/logs?output_format=text"
        response = self._request("GET", path)
        return response.text

    def list_workflow_files(self, workflow_name: str) -> dict[str, Any]:
        """List files in a workflow.

        Args:
            workflow_name: Name of the workflow

        Returns:
            List of files
        """
        response = self._request("GET", f"/workflows/{workflow_name}/files")
        return response.json()

    def get_workflow_file(self, workflow_name: str, file_path: str) -> dict[str, Any]:
        """Get content of a specific workflow file.

        Args:
            workflow_name: Name of the workflow
            file_path: Path to file within workflow

        Returns:
            File content
        """
        response = self._request(
            "GET",
            f"/workflows/{workflow_name}/files/{file_path}",
        )
        return response.json()

    def delete_workflow_file(
        self, workflow_name: str, file_path: str
    ) -> dict[str, Any]:
        """Delete a specific file from a workflow.

        Args:
            workflow_name: Name of the workflow
            file_path: Path to file within workflow

        Returns:
            Updated workflow data
        """
        return self.update_workflow(workflow_name, delete_files=[file_path])

    def stream_run_logs(
        self,
        resource_type: str,
        resource_name: str,
        run_number: int,
    ) -> Generator[dict[str, Any], None, None]:
        """Stream logs from a run via SSE.

        Args:
            resource_type: Either "workflow" or "model"
            resource_name: Name of the workflow or model
            run_number: Run number

        Yields:
            Log entries as dicts with 'logs' key containing batched log entries
        """
        # Use /logs endpoint (SSE is now the default format)
        path = f"/workspaces/{self._workspace_name}/{resource_type}s/{resource_name}/runs/{run_number}/logs"
        url = f"{self._get_platform_url()}{path}"
        headers = self._get_auth_headers()

        timeout = httpx.Timeout(connect=30.0, read=300.0, write=30.0, pool=30.0)
        with httpx.Client(timeout=timeout) as http_client:
            with http_client.stream("GET", url, headers=headers) as response:
                if response.status_code != 200:
                    error_body = response.read().decode()[:500]
                    yield {
                        "_error": True,
                        "status_code": response.status_code,
                        "body": error_body,
                    }
                    return

                for line in response.iter_lines():
                    if not line:
                        continue

                    if line.startswith("event:"):
                        event_type = line[6:].strip()
                        if event_type == "done":
                            return
                        continue

                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        try:
                            data = json.loads(data_str)
                            yield data
                        except json.JSONDecodeError:
                            pass

    # Authentication operations
    def authenticate_browser(self) -> str:
        """Authenticate using browser-based OAuth flow."""
        return auth_utils.authenticate_browser(get_config, self._make_request_for_auth)

    def authenticate_with_token(self, token: str, provider: str) -> str:
        """Authenticate using OAuth token (GitHub or Google)."""
        return auth_utils.authenticate_with_token(
            token, provider, get_config, self._make_request_for_auth
        )

    def authenticate_github(self, access_token: str) -> str:
        """Authenticate using GitHub access token."""
        return auth_utils.authenticate_github(
            access_token, get_config, self._make_request_for_auth
        )

    def authenticate_google(self, id_token: str) -> str:
        """Authenticate using Google ID token."""
        return auth_utils.authenticate_google(
            id_token, get_config, self._make_request_for_auth
        )

    def _make_request_for_auth(
        self, method: str, path: str, **kwargs
    ) -> httpx.Response:
        """Helper method for authentication flows that don't need full client setup."""
        # This is a simpler version used during auth flows before client is fully initialized
        with httpx.Client(timeout=30.0) as client:
            url = f"{self._get_platform_url()}{path}"
            response = client.request(method, url, **kwargs)
            if response.status_code != 200:
                try:
                    error_detail = response.json().get("detail", response.text)
                except:
                    error_detail = response.text
                raise Exception(f"Auth error ({response.status_code}): {error_detail}")
            return response


def sandbox(
    image: str | None = None,
    gpu: str | None = None,
    cpu: int | None = None,
    memory: int | None = None,
    timeout: int | None = None,
    idle_timeout: int | None = None,
    cloud: str | None = None,
    region: str | None = None,
    ephemeral_disk: int | None = None,
    block_network: bool | None = None,
    num_nodes: int | None = None,
    mixtrain_version: str | None = None,
) -> dict[str, Any]:
    """Configure the execution sandbox for a MixFlow workflow or MixModel.

    This function defines the compute environment where the workflow/model runs.
    Use it as a class attribute named `_sandbox` to configure resources.

    Args:
        image: Docker image to use (e.g., "pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime")
        gpu: GPU type (e.g., "A100", "H100", "T4", "L4")
        cpu: Number of CPU cores
        memory: Memory in MB (e.g., 32768 for 32GB)
        timeout: Maximum execution time in seconds
        idle_timeout: Idle timeout in seconds before container is stopped
        cloud: Cloud provider (e.g., "gcp", "aws")
        region: Cloud region (e.g., "us-east1", "us-west-2")
        ephemeral_disk: Ephemeral disk size in GB
        block_network: Whether to block network access
        num_nodes: Number of nodes for distributed training
        mixtrain_version: Mixtrain SDK version to install (e.g., "0.1.23", ">=0.1.20")

    Returns:
        Dict with sandbox configuration (non-None values only)

    Example:
        ```python
        from mixtrain import MixModel, sandbox

        class MyModel(MixModel):
            _sandbox = sandbox(
                image="pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime",
                gpu="A100",
                memory=32768,
                timeout=3600,
                mixtrain_version="0.1.23",
            )

            def run(self, prompt: str):
                '''Process the prompt.

                Args:
                    prompt: Text prompt to process
                '''
                return {"result": process(prompt)}
        ```

    Note:
        Only non-None values are included in the configuration.
        The sandbox configuration is extracted when the workflow/model is created
        and used to provision the execution environment.
    """
    config = {}
    if image is not None:
        config["image"] = image
    if gpu is not None:
        config["gpu"] = gpu
    if cpu is not None:
        config["cpu"] = cpu
    if memory is not None:
        config["memory"] = memory
    if timeout is not None:
        config["timeout"] = timeout
    if idle_timeout is not None:
        config["idle_timeout"] = idle_timeout
    if cloud is not None:
        config["cloud"] = cloud
    if region is not None:
        config["region"] = region
    if ephemeral_disk is not None:
        config["ephemeral_disk"] = ephemeral_disk
    if block_network is not None:
        config["block_network"] = block_network
    if num_nodes is not None:
        config["num_nodes"] = num_nodes
    if mixtrain_version is not None:
        config["mixtrain_version"] = mixtrain_version
    return config


class MixFlow:
    """Base class for workflows.

    Define inputs as parameters in the run() method signature:

    Example:
        ```python
        from mixtrain import MixFlow

        class MyWorkflow(MixFlow):
            def run(self, learning_rate: float = 0.001, epochs: int = 10):
                '''Train the model.

                Args:
                    learning_rate: Learning rate
                    epochs: Number of epochs
                '''
                print(f"Training with lr={learning_rate} for {epochs} epochs")
                return {"status": "completed"}
        ```

    Both calling styles work:
        - workflow.run(learning_rate=0.01, epochs=5)
        - workflow.run({"learning_rate": 0.01, "epochs": 5})
    """

    # Class-level metadata set by __init_subclass__
    _mixtrain_valid_inputs: set[str] = set()
    _mixtrain_required_inputs: set[str] = set()
    _mixtrain_input_defaults: dict[str, Any] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Wrap setup() to be idempotent
        if "setup" in cls.__dict__:
            original_setup = cls.__dict__["setup"]
            if not getattr(original_setup, "_mixtrain_wrapped", False):

                @functools.wraps(original_setup)
                def wrapped_setup(self, **kwargs):
                    if getattr(self, "_mixtrain_setup_done", False):
                        return  # Already called
                    self._mixtrain_setup_done = True
                    # Filter kwargs to only those the original setup accepts
                    setup_sig = inspect.signature(original_setup)
                    setup_params = set(setup_sig.parameters.keys()) - {"self"}
                    filtered_kwargs = {
                        k: v for k, v in kwargs.items() if k in setup_params
                    }
                    return original_setup(self, **filtered_kwargs)

                wrapped_setup._mixtrain_wrapped = True
                cls.setup = wrapped_setup

        # Wrap run()
        if "run" in cls.__dict__:
            original_run = cls.__dict__["run"]
            if getattr(original_run, "_mixtrain_wrapped", False):
                return

            # Extract inputs from run() signature
            sig = inspect.signature(original_run)
            valid_inputs = set()
            required_inputs = set()
            input_defaults = {}

            for name, param in sig.parameters.items():
                if name == "self":
                    continue
                valid_inputs.add(name)
                if param.default == inspect.Parameter.empty:
                    required_inputs.add(name)
                else:
                    input_defaults[name] = param.default

            cls._mixtrain_valid_inputs = valid_inputs
            cls._mixtrain_required_inputs = required_inputs
            cls._mixtrain_input_defaults = input_defaults

            # Get setup() signature to know which inputs it accepts
            setup_method = getattr(cls, "setup", None)
            setup_params = set()
            if setup_method:
                try:
                    setup_sig = inspect.signature(setup_method)
                    setup_params = set(setup_sig.parameters.keys()) - {"self"}
                except (ValueError, TypeError):
                    pass

            @functools.wraps(original_run)
            def wrapped_run(self, inputs: dict[str, Any] | None = None, **kwargs):
                # Merge dict and kwargs
                all_inputs = {**(inputs or {}), **kwargs}

                # Validate inputs
                if (
                    cls._mixtrain_valid_inputs
                ):  # Only validate if we have declared inputs
                    invalid = set(all_inputs.keys()) - cls._mixtrain_valid_inputs
                    if invalid:
                        raise ValueError(
                            f"Unknown inputs: {invalid}. Valid: {cls._mixtrain_valid_inputs}"
                        )

                    missing = cls._mixtrain_required_inputs - set(all_inputs.keys())
                    if missing:
                        raise ValueError(f"Missing required inputs: {missing}")

                # Apply defaults
                for name, default in cls._mixtrain_input_defaults.items():
                    if name not in all_inputs:
                        all_inputs[name] = default

                # Call setup (idempotent - no-op if already called by launcher)
                setup_kwargs = {
                    k: v for k, v in all_inputs.items() if k in setup_params
                }
                self.setup(**setup_kwargs)

                # Call run and cleanup
                try:
                    return original_run(self, **all_inputs)
                finally:
                    try:
                        self.cleanup()
                    except Exception as e:
                        # Log cleanup errors but don't let them mask the original exception
                        logger.warning(f"Cleanup error: {e}")

            wrapped_run._mixtrain_wrapped = True
            cls.run = wrapped_run

    def __init__(self):
        self.mix = MixClient()
        self._mixtrain_setup_done = False

    def setup(self, **kwargs):
        """Initialize the workflow. Override this method to perform setup operations.

        Can optionally receive inputs that are declared in the method signature.
        """
        pass

    def run(self, **kwargs):
        """Main execution method. Override this to implement workflow logic.

        Define inputs as method parameters. Both call styles are supported:
        - model.run(prompt="hello", temperature=0.7)
        - model.run({"prompt": "hello", "temperature": 0.7})

        Returns:
            Workflow outputs (typically a dict)
        """
        raise NotImplementedError(
            "Run method should be implemented by the workflow subclass"
        )

    def cleanup(self):
        """Clean up resources after workflow execution. Override this method if needed."""
        pass


class MixModel(MixFlow):
    """Base class for models, extends MixFlow.

    Models are a special type of workflow optimized for inference operations.
    They support run() for single inference and run_batch() for batch processing.

    Define inputs as parameters in the run() method signature:

    Example:
        ```python
        from mixtrain import MixModel

        class TextGenerationModel(MixModel):
            def setup(self):
                # Load model weights (called once)
                self.model = load_model()

            def run(self, prompt: str, temperature: float = 0.7, max_tokens: int = 512):
                '''Generate text from a prompt.

                Args:
                    prompt: Text prompt to generate from
                    temperature: Sampling temperature
                    max_tokens: Maximum tokens to generate
                '''
                result = self.model.generate(prompt, temperature=temperature, max_tokens=max_tokens)
                return {"generated_text": result}

            def cleanup(self):
                del self.model
        ```

    Both calling styles work:
        - model.run(prompt="hello", temperature=0.7)
        - model.run({"prompt": "hello", "temperature": 0.7})
    """

    def run(self, **kwargs):
        """Main inference method.

        Define inputs as method parameters. Returns model outputs (typically a dict).
        """
        raise NotImplementedError(
            "Run method must be implemented by the model subclass"
        )

    def run_batch(self, batch: list[dict[str, Any]]):
        """Batch inference method.

        Args:
            batch: List of input dictionaries.

        Returns:
            List of output dictionaries
        """
        results = []
        for item in batch:
            # Call run with each item's inputs
            results.append(self.run(**item))
        return results
