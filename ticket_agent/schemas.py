"""Schema definitions and helpers for the ticket triage agent."""

from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

# Candidate categorical values kept tight to support crisp accuracy scoring.
TicketCategory = Literal["bug", "incident", "request", "question"]
TicketSeverity = Literal["low", "medium", "high", "critical"]

class TicketTask(BaseModel):
    """Incoming task payload for the ticket triage agent."""

    model_config = ConfigDict(extra="forbid")

    ticket_id: str = Field(..., min_length=1, description="Stable identifier for the source ticket.")
    title: str = Field(..., min_length=1, description="Short summary provided by the reporter.")
    description: str = Field(..., min_length=1, description="Full ticket body including relevant context.")
    metadata: dict[str, str] | None = Field(
        default=None,
        description="Optional key/value metadata (e.g., product area, reporter role).",
    )

class TicketResult(BaseModel):
    """Structured response produced by the ticket triage agent."""

    model_config = ConfigDict(extra="forbid")

    category: TicketCategory = Field(..., description="Canonical ticket type chosen from the allowed taxonomy.")
    severity: TicketSeverity = Field(..., description="Impact level aligned with the triage playbook.")
    next_step: str = Field(..., min_length=1, description="Actionable recommendation for the on-call or assignee.")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Model confidence score bounded between 0 and 1 inclusive."
    )

def task_json_schema() -> dict[str, Any]:
    """Return the JSON schema for the task payload."""

    return TicketTask.model_json_schema()

def result_json_schema() -> dict[str, Any]:
    """Return the JSON schema for the result payload."""

    return TicketResult.model_json_schema()
