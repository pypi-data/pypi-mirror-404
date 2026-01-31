"""Router proxy class for convenient router access and operations.

This module provides a Router proxy class that makes it easy to reference
and interact with routers in a workspace.

Example:
    >>> from mixtrain import get_router, Router
    >>> router = get_router("my-router")
    >>> result = router.route({"user": {"tier": "premium"}})
    >>> print(result.matched_rule.name)
"""

import json
import logging
from typing import Any

from .client import MixClient
from .helpers import validate_resource_name
from .routing.engine import RoutingEngine, RoutingEngineFactory
from .routing.models import RoutingResult

logger = logging.getLogger(__name__)


def _detect_rule_changes(
    old_rules: list[dict[str, Any]], new_rules: list[dict[str, Any]]
) -> str:
    """Detect changes between rule sets and generate a change message."""

    def rules_are_equal(rule1: dict[str, Any], rule2: dict[str, Any]) -> bool:
        """Compare two rules ignoring ID fields."""
        clean1 = {k: v for k, v in rule1.items() if k != "id"}
        clean2 = {k: v for k, v in rule2.items() if k != "id"}
        return json.dumps(clean1, sort_keys=True) == json.dumps(clean2, sort_keys=True)

    def get_rule_name(rule: dict[str, Any], index: int) -> str:
        return rule.get("name") or f"Rule {index + 1}"

    if not old_rules:
        if new_rules:
            rule_names = [get_rule_name(rule, i) for i, rule in enumerate(new_rules)]
            return f"Added {', '.join(rule_names)}"
        return "Initial configuration"

    if not new_rules:
        rule_names = [get_rule_name(rule, i) for i, rule in enumerate(old_rules)]
        return f"Deleted all rules ({', '.join(rule_names)})"

    old_len, new_len = len(old_rules), len(new_rules)
    edited, added, deleted = [], [], []

    # Compare rules that exist in both
    for i in range(min(old_len, new_len)):
        if not rules_are_equal(old_rules[i], new_rules[i]):
            edited.append(get_rule_name(new_rules[i], i))

    # Rules added (new list is longer)
    for i in range(old_len, new_len):
        added.append(get_rule_name(new_rules[i], i))

    # Rules deleted (old list was longer)
    for i in range(new_len, old_len):
        deleted.append(get_rule_name(old_rules[i], i))

    changes = []
    if edited:
        changes.append(f"Edited {', '.join(edited)}")
    if added:
        changes.append(f"Added {', '.join(added)}")
    if deleted:
        changes.append(f"Deleted {', '.join(deleted)}")

    return "; ".join(changes) if changes else "No changes"


class Router:
    """Proxy class for convenient router access and operations.

    This class provides a clean, object-oriented interface for working with
    routers. The RoutingEngine is used internally for routing evaluation.

    Args:
        name: Name of the router
        client: Optional MixClient instance (creates new one if not provided)

    Attributes:
        name: Router name
        client: MixClient instance for API operations

    Example:
        >>> router = Router("my-router")
        >>> result = router.route({"user": {"tier": "premium"}})
        >>> print(result.matched_rule.name)
        >>> print(router.rules)
    """

    def __init__(self, name: str, client: MixClient | None = None):
        """Initialize Router proxy.

        Args:
            name: Name of the router
            client: Optional MixClient instance (creates new one if not provided)

        Raises:
            ValueError: If name is invalid (must be lowercase alphanumeric with hyphens/underscores)
        """
        validate_resource_name(name, "router")
        self.name = name
        self.client = client or MixClient()
        self._config: dict[str, Any] | None = None
        self._engine: RoutingEngine = self._create_engine()  # Eager load

    def _create_engine(self) -> RoutingEngine:
        """Internal: Create routing engine from fetched config."""
        config = self._fetch_config()
        return RoutingEngineFactory.from_json(config)

    def _fetch_config(self, version: int | None = None) -> dict[str, Any]:
        """Internal: Fetch config directly via HTTP."""
        params = {"version": version} if version else None
        response = self.client._request(
            "GET",
            f"/inference/routers/{self.name}",
            params=params,
        )
        config = response.json()
        # Cache the config
        if version is None:
            self._config = config
        return config

    # === Properties ===

    @property
    def config(self) -> dict[str, Any]:
        """Get current router configuration (cached).

        Returns:
            Full router configuration including rules, metadata, etc.

        Example:
            >>> router = Router("my-router")
            >>> print(router.config["description"])
        """
        if self._config is None:
            self._config = self._fetch_config()
        return self._config

    @property
    def rules(self) -> list[dict[str, Any]]:
        """Get current routing rules (shortcut to config['rules']).

        Returns:
            List of routing rules

        Example:
            >>> router = Router("my-router")
            >>> for rule in router.rules:
            ...     print(f"{rule['name']}: priority {rule['priority']}")
        """
        return self.config.get("rules", [])

    @property
    def versions(self) -> list[dict[str, Any]]:
        """Get all configuration versions.

        Returns:
            List of version records with version number, created_at, etc.

        Example:
            >>> router = Router("my-router")
            >>> for v in router.versions:
            ...     print(f"Version {v['version']}: {v['change_message']}")
        """
        response = self.client._request(
            "GET",
            f"/inference/routers/{self.name}/versions",
        )
        return response.json().get("data", [])

    @property
    def active_version(self) -> int | None:
        """Get currently deployed version number.

        Returns:
            Active version number or None if not deployed

        Example:
            >>> router = Router("my-router")
            >>> print(f"Active version: {router.active_version}")
        """
        return self.config.get("active_version")

    # === Core Operations ===

    def route(self, request_data: dict[str, Any]) -> RoutingResult:
        """Route a request using the eager-loaded routing engine.

        Args:
            request_data: The request data to route (e.g., user info, model name)

        Returns:
            RoutingResult with matched rule, selected targets, and explanation

        Example:
            >>> router = Router("my-router")
            >>> result = router.route({"user": {"tier": "premium"}})
            >>> if result.matched_rule:
            ...     print(f"Matched: {result.matched_rule.name}")
            ...     for target in result.selected_targets:
            ...         print(f"  -> {target.endpoint}")
        """
        return self._engine.route_request(request_data)

    # === CRUD Operations ===

    def update(
        self,
        rules: list[dict[str, Any]] | None = None,
        description: str | None = None,
        settings: dict[str, Any] | None = None,
        change_message: str | None = None,
    ) -> dict[str, Any]:
        """Update router configuration (creates a new version).

        Args:
            rules: Optional new rules list
            description: Optional new description
            settings: Optional deployment settings (inference_uri, update_uri)
            change_message: Optional change summary message

        Returns:
            Updated router configuration

        Example:
            >>> router = Router("my-router")
            >>> router.update(
            ...     rules=[...],
            ...     change_message="Added premium tier rule"
            ... )
        """
        payload: dict[str, Any] = {}
        if description is not None:
            payload["description"] = description
        if settings is not None:
            payload["settings"] = settings
        if rules is not None:
            payload["rules"] = rules
            # Auto-generate change message if not provided
            if change_message:
                payload["change_message"] = change_message
            else:
                old_rules = self.rules
                payload["change_message"] = _detect_rule_changes(old_rules, rules)

        response = self.client._request(
            "PUT",
            f"/inference/routers/{self.name}",
            json=payload,
        )
        # Refresh config and engine
        self.refresh()
        return response.json()

    def deploy(self, version: int | None = None) -> dict[str, Any]:
        """Deploy/activate a router configuration version.

        This sets the specified version as the active deployment and
        notifies the router's update_uri (if configured) to reload config.

        Args:
            version: Optional specific version to deploy (defaults to latest)

        Returns:
            Deployment result with version info

        Example:
            >>> router = Router("my-router")
            >>> router.deploy()  # Deploy latest
            >>> router.deploy(version=3)  # Deploy specific version
        """
        payload: dict[str, Any] = {}
        if version is not None:
            payload["version"] = version

        response = self.client._request(
            "POST",
            f"/inference/routers/{self.name}/activate",
            json=payload,
        )
        # Refresh config
        self.refresh()
        return response.json()

    def delete(self) -> dict[str, Any]:
        """Delete this router and all its versions.

        Returns:
            Deletion result

        Example:
            >>> router = Router("my-router")
            >>> router.delete()
        """
        response = self.client._request(
            "DELETE",
            f"/inference/routers/{self.name}",
        )
        return response.json()

    # === Request History ===

    def list_requests(
        self,
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
        matched_rule: str | None = None,
        response_code: str | None = None,
    ) -> dict[str, Any]:
        """List routed requests with pagination and filtering.

        Args:
            limit: Maximum number of requests to return (default: 20)
            offset: Number of requests to skip (for pagination)
            status: Filter by status (e.g., "completed", "failed")
            matched_rule: Filter by matched rule name
            response_code: Filter by response code (e.g., "200", "4xx", "5xx")

        Returns:
            Dict with 'requests' list and 'total' count

        Example:
            >>> router = Router("my-router")
            >>> result = router.list_requests(limit=50, status="completed")
            >>> for req in result["requests"]:
            ...     print(f"{req['request_id']}: {req['matched_rule_name']}")
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if matched_rule is not None:
            params["matched_rule"] = matched_rule
        if response_code:
            params["response_code"] = response_code

        response = self.client._request(
            "GET",
            f"/inference/routers/{self.name}/requests",
            params=params,
        )
        return response.json()

    def get_request(self, request_id: str) -> dict[str, Any]:
        """Get details of a specific routed request.

        Args:
            request_id: UUID of the request

        Returns:
            Request details including input, routing result, response, etc.

        Example:
            >>> router = Router("my-router")
            >>> req = router.get_request("uuid-123")
            >>> print(req["matched_rule_name"])
            >>> print(req["response_status_code"])
        """
        response = self.client._request(
            "GET",
            f"/inference/routers/{self.name}/requests/{request_id}",
        )
        return response.json()

    def create_request(
        self,
        input_request: dict[str, Any],
        status: str | None = None,
        matched_rule_name: str | None = None,
        routing_result: dict[str, Any] | None = None,
        selected_target: dict[str, Any] | None = None,
        response_data: dict[str, Any] | None = None,
        response_status_code: int | None = None,
        error_message: str | None = None,
        routing_latency_ms: float | None = None,
        execution_latency_ms: float | None = None,
        total_latency_ms: float | None = None,
        invocation_type: str | None = None,
        invoked_model_run_number: int | None = None,
        invoked_workflow_run_number: int | None = None,
    ) -> dict[str, Any]:
        """Create a router request log entry.

        Used by external systems to log requests processed outside the platform.

        Args:
            input_request: The original request payload
            status: Initial status (pending, routing, executing, completed, failed)
            matched_rule_name: Name of the matched routing rule
            routing_result: Full routing decision result
            selected_target: Selected target endpoint
            response_data: Response from target
            response_status_code: HTTP response status code
            error_message: Error message if failed
            routing_latency_ms: Time spent on routing decision
            execution_latency_ms: Time spent on execution
            total_latency_ms: Total request latency
            invocation_type: Type of downstream invocation (model, workflow, external)
            invoked_model_run_number: Run number of invoked model run
            invoked_workflow_run_number: Run number of invoked workflow run

        Returns:
            Created router request details

        Example:
            >>> router = Router("my-router")
            >>> req = router.create_request(
            ...     input_request={"user": {"tier": "premium"}},
            ...     status="completed",
            ...     matched_rule_name="premium-route",
            ...     response_status_code=200,
            ... )
        """
        payload: dict[str, Any] = {"input_request": input_request}
        if status:
            payload["status"] = status
        if matched_rule_name:
            payload["matched_rule_name"] = matched_rule_name
        if routing_result:
            payload["routing_result"] = routing_result
        if selected_target:
            payload["selected_target"] = selected_target
        if response_data:
            payload["response_data"] = response_data
        if response_status_code:
            payload["response_status_code"] = response_status_code
        if error_message:
            payload["error_message"] = error_message
        if routing_latency_ms:
            payload["routing_latency_ms"] = routing_latency_ms
        if execution_latency_ms:
            payload["execution_latency_ms"] = execution_latency_ms
        if total_latency_ms:
            payload["total_latency_ms"] = total_latency_ms
        if invocation_type:
            payload["invocation_type"] = invocation_type
        if invoked_model_run_number:
            payload["invoked_model_run_number"] = invoked_model_run_number
        if invoked_workflow_run_number:
            payload["invoked_workflow_run_number"] = invoked_workflow_run_number

        response = self.client._request(
            "POST",
            f"/inference/routers/{self.name}/requests",
            json=payload,
        )
        return response.json()

    # === Utility ===

    def refresh(self):
        """Re-fetch config and re-create engine.

        Use this after external changes to the router configuration.

        Example:
            >>> router = Router("my-router")
            >>> router.refresh()
            >>> print(router.config)  # Fresh data
        """
        self._config = None
        self._engine = self._create_engine()

    def __repr__(self) -> str:
        """String representation of the Router."""
        return f"Router(name='{self.name}')"

    def __str__(self) -> str:
        """Human-readable string representation."""
        active = self.active_version
        return f"Router: {self.name} (v{active})" if active else f"Router: {self.name}"

    # === Factory Methods ===

    @classmethod
    def get(cls, name: str, client: MixClient | None = None) -> "Router":
        """Get a router by name (primary access method).

        Args:
            name: Router name
            client: Optional MixClient instance

        Returns:
            Router proxy instance

        Example:
            >>> router = Router.get("my-router")
            >>> result = router.route({"user": {"tier": "premium"}})
        """
        return cls(name, client=client)

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        rules: list[dict[str, Any]],
        settings: dict[str, Any] | None = None,
        client: MixClient | None = None,
    ) -> "Router":
        """Create a new router.

        Args:
            name: Router name (must be unique in workspace)
            description: Router description
            rules: List of routing rules
            settings: Optional deployment settings (inference_uri, update_uri)
            client: Optional MixClient instance

        Returns:
            Router proxy instance for the created router

        Example:
            >>> router = Router.create(
            ...     name="ab-test-router",
            ...     description="A/B test between models",
            ...     rules=[
            ...         {"name": "premium", "priority": 100, ...},
            ...         {"name": "default", "priority": 1, ...},
            ...     ]
            ... )
        """
        c = client or MixClient()
        payload: dict[str, Any] = {
            "name": name,
            "description": description,
            "rules": rules,
        }
        if settings:
            payload["settings"] = settings

        c._request(
            "POST",
            "/inference/routers",
            json=payload,
        )
        return cls(name, client=c)

    @classmethod
    def list(
        cls, status: str | None = None, client: MixClient | None = None
    ) -> list[dict[str, Any]]:
        """List all routers in workspace.

        Returns router summary data without loading full configurations.
        Use Router.get(name) to get a specific router with full config.

        Args:
            status: Optional filter by status ('active', 'inactive')
            client: Optional MixClient instance

        Returns:
            List of router summary dicts with name, description, active_version, etc.

        Example:
            >>> for r in Router.list():
            ...     print(f"{r['name']}: v{r.get('active_version')}")
            >>> # Get full router for a specific one
            >>> router = Router.get("my-router")
        """
        c = client or MixClient()
        params = {"status": status} if status else None
        response = c._request(
            "GET",
            "/inference/routers",
            params=params,
        )
        return response.json().get("data", [])


# Module-level convenience functions


def get_router(name: str, client: MixClient | None = None) -> Router:
    """Get a router by name.

    This is the primary way to access routers in a workspace.

    Args:
        name: Router name
        client: Optional MixClient instance

    Returns:
        Router proxy instance

    Example:
        >>> from mixtrain import get_router
        >>> router = get_router("my-router")
        >>> result = router.route({"user": {"tier": "premium"}})
    """
    return Router.get(name, client=client)


def list_routers(
    status: str | None = None, client: MixClient | None = None
) -> list[dict[str, Any]]:
    """List all routers in the workspace.

    Returns router summary data without loading full configurations.
    Use get_router(name) to get a specific router with full config.

    Args:
        status: Optional filter by status ('active', 'inactive')
        client: Optional MixClient instance

    Returns:
        List of router summary dicts

    Example:
        >>> from mixtrain import list_routers, get_router
        >>> for r in list_routers():
        ...     print(r["name"])
        >>> router = get_router("my-router")  # Get full router
    """
    return Router.list(status=status, client=client)
