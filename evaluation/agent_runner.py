
"""Agent runner abstractions for the evaluation harness."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Protocol, runtime_checkable

from ticket_agent.schemas import TicketResult, TicketTask

from evaluation.types import AgentResponse, AgentRunMetadata


@dataclass(slots=True)
class RunContext:
    """Lightweight hook data passed to metadata callbacks."""

    task: TicketTask
    result: TicketResult
    elapsed_ms: float


@runtime_checkable
class AgentRunnerProtocol(Protocol):
    """Protocol implemented by agent runners used in evaluation."""

    def run(self, task: TicketTask) -> AgentResponse:
        """Execute the agent for a single task and return the structured response."""


AgentCallable = Callable[[TicketTask], TicketResult | AgentResponse]
MetadataHook = Callable[[RunContext], AgentRunMetadata]


class CallableAgentRunner(AgentRunnerProtocol):
    """Wraps a callable into an AgentRunner with basic instrumentation."""

    def __init__(
        self,
        agent_callable: AgentCallable,
        *,
        metadata_hook: MetadataHook | None = None,
    ) -> None:
        self._callable = agent_callable
        self._metadata_hook = metadata_hook

    def run(self, task: TicketTask) -> AgentResponse:
        start = time.perf_counter()
        response = self._callable(task)
        elapsed_ms = (time.perf_counter() - start) * 1000

        if isinstance(response, AgentResponse):
            metadata = response.metadata
            # TODO: enrich latency/tokens via hooks once instrumentation lands elsewhere.
            if metadata.latency_ms is None:
                metadata.latency_ms = elapsed_ms
            return response

        result = response
        metadata = self._metadata_hook(RunContext(task, result, elapsed_ms)) if self._metadata_hook else AgentRunMetadata(latency_ms=elapsed_ms)
        return AgentResponse(result=result, metadata=metadata)


class NoOpAgentRunner(AgentRunnerProtocol):
    """Placeholder runner that raises to signify missing implementation."""

    def run(self, task: TicketTask) -> AgentResponse:  # pragma: no cover - defensive stub
        raise NotImplementedError("Agent runner is not configured. Provide a concrete implementation before evaluation.")

