from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DeploymentMetrics:
    p50: float = 0.0
    p99: float = 0.0
    rps: float = 0.0
    cost_per_1k: float = 0.0
    gpu_util: float = 0.0
    predicted_rps: float = 0.0


@dataclass
class Deployment:
    id: str = ""
    model: str = ""
    status: str = ""
    regions: list[str] = field(default_factory=list)
    replicas: int = 0
    metrics: DeploymentMetrics = field(default_factory=DeploymentMetrics)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Deployment:
        metrics_data = data.get("metrics", {})
        metrics = DeploymentMetrics(
            p50=metrics_data.get("p50", 0.0),
            p99=metrics_data.get("p99", 0.0),
            rps=metrics_data.get("rps", 0.0),
            cost_per_1k=metrics_data.get("cost_per_1k", 0.0),
            gpu_util=metrics_data.get("gpu_util", 0.0),
            predicted_rps=metrics_data.get("predicted_rps", 0.0),
        )
        return cls(
            id=data.get("id", ""),
            model=data.get("model", ""),
            status=data.get("status", ""),
            regions=data.get("regions", []),
            replicas=data.get("replicas", 0),
            metrics=metrics,
        )


@dataclass
class InferenceResponse:
    text: str = ""
    region: str = ""
    latency_ms: float = 0.0
    tokens_used: int = 0
    trace_id: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InferenceResponse:
        return cls(
            text=data.get("text", ""),
            region=data.get("region", ""),
            latency_ms=data.get("latency_ms", 0.0),
            tokens_used=data.get("tokens_used", 0),
            trace_id=data.get("trace_id", ""),
        )


@dataclass
class RoutingPolicy:
    id: str = ""
    objectives: list[str] = field(default_factory=list)
    weights: list[float] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)
    convergence_status: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RoutingPolicy:
        return cls(
            id=data.get("id", ""),
            objectives=data.get("objectives", []),
            weights=data.get("weights", []),
            constraints=data.get("constraints", {}),
            convergence_status=data.get("convergence_status", ""),
        )


@dataclass
class TelemetryDatapoint:
    timestamp: str = ""
    p99_latency: float = 0.0
    cost_per_1k: float = 0.0
    rps: float = 0.0
    drift_score: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TelemetryDatapoint:
        return cls(
            timestamp=data.get("timestamp", ""),
            p99_latency=data.get("p99_latency", 0.0),
            cost_per_1k=data.get("cost_per_1k", 0.0),
            rps=data.get("rps", 0.0),
            drift_score=data.get("drift_score", 0.0),
        )


@dataclass
class TelemetryResult:
    datapoints: list[TelemetryDatapoint] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TelemetryResult:
        points = [
            TelemetryDatapoint.from_dict(p) for p in data.get("datapoints", [])
        ]
        return cls(datapoints=points)
