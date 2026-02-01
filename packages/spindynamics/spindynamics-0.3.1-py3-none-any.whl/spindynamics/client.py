from __future__ import annotations

import os
from typing import Any

import httpx

from .exceptions import APIError, AuthenticationError, RateLimitError, SpinDynamicsError
from .resources import DeploymentsManager, RoutingManager, TelemetryManager
from .types import Deployment, InferenceResponse


class Cortex:
    """SpinDynamics API client."""

    DEFAULT_BASE_URL = "https://api.spindynamics.net"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("SPINDYNAMICS_API_KEY", "")
        if not self.api_key:
            raise SpinDynamicsError(
                "No API key provided. Pass api_key= or set SPINDYNAMICS_API_KEY."
            )
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self._http = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        self.deployments = DeploymentsManager(self)
        self.routing = RoutingManager(self)
        self.telemetry = TelemetryManager(self)

    def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> Any:
        response = self._http.request(method, path, json=json)
        request_id = response.headers.get("x-request-id")

        if response.status_code == 401:
            body = response.json()
            raise AuthenticationError(
                message=body.get("message", "Authentication failed"),
                error_code=body.get("error"),
                request_id=request_id,
            )

        if response.status_code == 429:
            body = response.json()
            raise RateLimitError(
                message=body.get("message", "Rate limit exceeded"),
                error_code=body.get("error"),
                request_id=request_id,
            )

        if response.status_code >= 400:
            body = response.json()
            raise APIError(
                message=body.get("message", "API request failed"),
                status_code=response.status_code,
                error_code=body.get("error"),
                request_id=request_id,
            )

        if response.status_code == 204:
            return {}
        return response.json()

    def deploy(
        self,
        model: str,
        strategy: str = "adaptive",
        regions: list[str] | None = None,
        constraints: dict[str, Any] | None = None,
        autoscale: dict[str, Any] | None = None,
    ) -> Deployment:
        payload: dict[str, Any] = {"model": model, "strategy": strategy}
        if regions is not None:
            payload["regions"] = regions
        if constraints is not None:
            payload["constraints"] = constraints
        if autoscale is not None:
            payload["autoscale"] = autoscale
        data = self._request("POST", "/v1/deployments", json=payload)
        return Deployment.from_dict(data)

    def infer(
        self,
        deployment_id: str,
        prompt: str,
        max_tokens: int = 512,
        stream: bool = False,
    ) -> InferenceResponse:
        payload: dict[str, Any] = {
            "deployment_id": deployment_id,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        data = self._request("POST", "/v1/infer", json=payload)
        return InferenceResponse.from_dict(data)
