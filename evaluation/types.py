"""Common type aliases and dataclasses used across evaluation modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ticket_agent.schemas import TicketResult, TicketTask


@dataclass(slots=True)
class AgentRunMetadata:
    """Telemetry captured from a single agent invocation."""

    latency_ms: float | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    usd_cost: float | None = None
    tool_calls: int | None = None
    retries: int | None = None
    cache_hit: bool | None = None
    failure_reason: str | None = None

    # TODO: add serialization helpers if we emit metadata to JSON logs.


@dataclass(slots=True)
class AgentResponse:
    """Wrapper around the agent result and associated metadata."""

    result: TicketResult
    metadata: AgentRunMetadata

    # TODO: consider carrying raw model/tool responses for debugging.


@dataclass(slots=True)
class EvalExample:
    """Bundled task and gold result used during evaluation."""

    task: TicketTask
    gold: TicketResult
    difficulty: str | None = None

    # TODO: add origin metadata (e.g., dataset filename, line number) for richer diagnostics.


@dataclass(slots=True)
class EvalResult:
    """Outcome of evaluating a single example."""

    ticket_id: str
    output: TicketResult
    metrics: dict[str, Any]
    metadata: AgentRunMetadata

    # TODO: include collected `EvaluationIssue` instances per example if needed.

