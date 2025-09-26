"""Issue reporting primitives for the evaluation harness."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class IssueType(str, Enum):
    """Classification of evaluation issues for CI reporting."""

    SCHEMA_FAILURE = "schema_failure"
    JOIN_MISMATCH = "join_mismatch"
    METRIC_REGRESSION = "metric_regression"
    # TODO: extend with additional categories as requirements emerge (e.g., tool_failure).


@dataclass(slots=True)
class EvaluationIssue:
    """Structured issue emitted by validators and the evaluation harness."""

    issue_type: IssueType
    details: str
    ticket_id: str | None = None
    metrics: dict[str, Any] | None = None
    severity: str = "ERROR"

    # TODO: add helper constructors (e.g., `schema_failure(...)`) to standardize message formats.
    # TODO: consider `timestamp` field if consumers need ordering information.

