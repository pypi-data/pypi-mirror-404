from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .client import Cortex
from .types import Deployment, RoutingPolicy, TelemetryResult


class DeploymentsManager:
    def __init__(self, client: Cortex) -> None:
        self._client = client

    def list(self) -> list[Deployment]:
        data = self._client._request("GET", "/v1/deployments")
        return [Deployment.from_dict(d) for d in data.get("deployments", [])]

    def get(self, deployment_id: str) -> Deployment:
        data = self._client._request("GET", f"/v1/deployments/{deployment_id}")
        return Deployment.from_dict(data)

    def update(self, deployment_id: str, **kwargs: Any) -> Deployment:
        data = self._client._request(
            "PATCH", f"/v1/deployments/{deployment_id}", json=kwargs
        )
        return Deployment.from_dict(data)

    def delete(self, deployment_id: str) -> None:
        self._client._request("DELETE", f"/v1/deployments/{deployment_id}")


class RoutingManager:
    def __init__(self, client: Cortex) -> None:
        self._client = client

    def create_policy(self, **kwargs: Any) -> RoutingPolicy:
        data = self._client._request("POST", "/v1/routing/policies", json=kwargs)
        return RoutingPolicy.from_dict(data)

    def list_policies(self) -> list[RoutingPolicy]:
        data = self._client._request("GET", "/v1/routing/policies")
        return [RoutingPolicy.from_dict(p) for p in data.get("policies", [])]

    def get_policy(self, policy_id: str) -> RoutingPolicy:
        data = self._client._request("GET", f"/v1/routing/policies/{policy_id}")
        return RoutingPolicy.from_dict(data)


class TelemetryManager:
    def __init__(self, client: Cortex) -> None:
        self._client = client

    def query(self, **kwargs: Any) -> TelemetryResult:
        data = self._client._request("POST", "/v1/telemetry/query", json=kwargs)
        return TelemetryResult.from_dict(data)

    def export(self, **kwargs: Any) -> dict[str, Any]:
        return self._client._request("POST", "/v1/telemetry/export", json=kwargs)

    def create_alert(self, **kwargs: Any) -> dict[str, Any]:
        return self._client._request("POST", "/v1/telemetry/alerts", json=kwargs)

    def alerts(self) -> list[dict[str, Any]]:
        data = self._client._request("GET", "/v1/telemetry/alerts")
        return data.get("alerts", [])
