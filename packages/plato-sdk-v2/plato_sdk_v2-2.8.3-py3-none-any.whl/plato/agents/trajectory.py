"""ATIF (Agent Trajectory Interchange Format) models.

This module provides Pydantic models for the ATIF specification,
a standardized format for logging agent interaction history.

Matches Harbor's trajectory format exactly for compatibility.
Spec: https://harborframework.com/docs/trajectory-format
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

SCHEMA_VERSION: Literal["ATIF-v1.0", "ATIF-v1.1", "ATIF-v1.2", "ATIF-v1.3", "ATIF-v1.4", "ATIF-v1.5"] = "ATIF-v1.5"


class Metrics(BaseModel):
    """LLM operational and confidence data."""

    model_config = {"extra": "forbid"}

    prompt_tokens: int | None = Field(default=None, description="Number of tokens in the prompt")
    completion_tokens: int | None = Field(default=None, description="Number of tokens in the completion")
    cached_tokens: int | None = Field(default=None, description="Number of cached tokens used")
    cost_usd: float | None = Field(default=None, description="Cost in USD for this step")
    prompt_token_ids: list[int] | None = Field(default=None, description="Token IDs for the prompt")
    completion_token_ids: list[int] | None = Field(default=None, description="Token IDs for the completion")
    logprobs: list[float] | None = Field(default=None, description="Log probabilities for completion tokens")
    extra: dict[str, Any] | None = Field(default=None, description="Custom metrics")


class FinalMetrics(BaseModel):
    """Trajectory-level aggregate statistics."""

    model_config = {"extra": "forbid"}

    total_prompt_tokens: int | None = Field(
        default=None,
        description="Sum of all prompt tokens across all steps, including cached tokens",
    )
    total_completion_tokens: int | None = Field(
        default=None,
        description="Sum of all completion tokens across all steps",
    )
    total_cached_tokens: int | None = Field(
        default=None,
        description="Sum of all cached tokens across all steps",
    )
    total_cost_usd: float | None = Field(
        default=None,
        description="Total real monetary cost for the entire trajectory",
    )
    total_steps: int | None = Field(
        default=None,
        ge=0,
        description="Number of steps in the trajectory",
    )
    extra: dict[str, Any] | None = Field(default=None, description="Custom aggregate metrics")


class ToolCall(BaseModel):
    """A function/tool invocation."""

    model_config = {"extra": "forbid"}

    tool_call_id: str = Field(..., description="Unique identifier for this specific tool call")
    function_name: str = Field(..., description="The name of the function or tool being invoked")
    arguments: dict[str, Any] = Field(..., description="Arguments passed to the function (can be empty dict)")


class ObservationResult(BaseModel):
    """Result from a single tool call."""

    model_config = {"extra": "forbid"}

    source_call_id: str = Field(..., description="ID of the tool call that produced this result")
    content: str = Field(..., description="The result content from the tool execution")


class Observation(BaseModel):
    """Environment feedback from tool execution."""

    model_config = {"extra": "forbid"}

    results: list[ObservationResult] = Field(..., description="Results from tool executions")


class Step(BaseModel):
    """A single interaction step in the trajectory."""

    model_config = {"extra": "forbid"}

    step_id: int = Field(..., ge=1, description="Ordinal index of the turn (starting from 1)")
    timestamp: str | None = Field(default=None, description="ISO 8601 timestamp")
    source: Literal["user", "agent", "system"] = Field(..., description="Step originator")
    message: str = Field(..., description="Dialogue content (allows empty string)")

    # Agent-only fields
    model_name: str | None = Field(default=None, description="LLM model used for this step")
    reasoning_effort: str | float | None = Field(default=None, description="Effort measurement")
    reasoning_content: str | None = Field(default=None, description="Agent's internal reasoning")
    tool_calls: list[ToolCall] | None = Field(default=None, description="Structured action objects")
    observation: Observation | None = Field(default=None, description="Environment feedback")
    metrics: Metrics | None = Field(default=None, description="LLM operational and confidence data")
    is_copied_context: bool | None = Field(default=None, description="Context reuse indicator (ATIF-v1.5+)")

    # Custom metadata
    extra: dict[str, Any] | None = Field(default=None, description="Custom metadata")

    @classmethod
    def user(cls, step_id: int, message: str, **kwargs: Any) -> Step:
        """Create a user step."""
        return cls(
            step_id=step_id,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            source="user",
            message=message,
            **kwargs,
        )

    @classmethod
    def agent(
        cls,
        step_id: int,
        message: str,
        model_name: str,
        tool_calls: list[ToolCall] | None = None,
        observation: Observation | None = None,
        metrics: Metrics | None = None,
        reasoning_content: str | None = None,
        **kwargs: Any,
    ) -> Step:
        """Create an agent step."""
        return cls(
            step_id=step_id,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            source="agent",
            message=message,
            model_name=model_name,
            tool_calls=tool_calls,
            observation=observation,
            metrics=metrics,
            reasoning_content=reasoning_content,
            **kwargs,
        )

    @classmethod
    def system(cls, step_id: int, message: str, **kwargs: Any) -> Step:
        """Create a system step."""
        return cls(
            step_id=step_id,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            source="system",
            message=message,
            **kwargs,
        )


class Agent(BaseModel):
    """Agent metadata."""

    model_config = {"extra": "forbid"}

    name: str = Field(..., description="The name of the agent system")
    version: str = Field(..., description="The version identifier of the agent system")
    model_name: str | None = Field(default=None, description="Default LLM model used for this trajectory")
    tool_definitions: list[dict[str, Any]] | None = Field(
        default=None,
        description="Array of tool/function definitions available to the agent",
    )
    extra: dict[str, Any] | None = Field(default=None, description="Custom agent configuration details")


class Trajectory(BaseModel):
    """ATIF trajectory - the complete interaction history.

    Example:
        trajectory = Trajectory(
            session_id="abc-123",
            agent=Agent(name="openhands", version="0.37.0", model_name="claude-sonnet-4"),
            steps=[
                Step.user(1, "Fix the bug in main.py"),
                Step.agent(2, "I'll analyze the code...", model_name="claude-sonnet-4"),
            ],
        )
        trajectory.to_file("/logs/agent/trajectory.json")
    """

    model_config = {"extra": "forbid"}

    schema_version: Literal["ATIF-v1.0", "ATIF-v1.1", "ATIF-v1.2", "ATIF-v1.3", "ATIF-v1.4", "ATIF-v1.5"] = Field(
        default="ATIF-v1.5",
        description="String defining ATIF compatibility",
    )
    session_id: str = Field(..., description="Unique identifier for the entire agent run")
    agent: Agent = Field(..., description="Object specifying the agent configuration")
    steps: list[Step] = Field(
        ..., min_length=1, description="Array of step objects representing the complete interaction history"
    )
    notes: str | None = Field(default=None, description="Custom information, design notes, or explanations")
    final_metrics: FinalMetrics | None = Field(default=None, description="Summary metrics for the entire trajectory")
    continued_trajectory_ref: str | None = Field(
        default=None,
        description="Reference to continuation trajectory file if this trajectory is continued elsewhere",
    )
    extra: dict[str, Any] | None = Field(default=None, description="Custom root-level metadata")

    def add_step(self, step: Step) -> None:
        """Add a step to the trajectory."""
        self.steps.append(step)

    def compute_final_metrics(self) -> FinalMetrics:
        """Compute aggregate metrics from all steps."""
        total_prompt = 0
        total_completion = 0
        total_cached = 0
        total_cost = 0.0

        for step in self.steps:
            if step.metrics:
                if step.metrics.prompt_tokens:
                    total_prompt += step.metrics.prompt_tokens
                if step.metrics.completion_tokens:
                    total_completion += step.metrics.completion_tokens
                if step.metrics.cached_tokens:
                    total_cached += step.metrics.cached_tokens
                if step.metrics.cost_usd:
                    total_cost += step.metrics.cost_usd

        self.final_metrics = FinalMetrics(
            total_prompt_tokens=total_prompt if total_prompt > 0 else None,
            total_completion_tokens=total_completion if total_completion > 0 else None,
            total_steps=len(self.steps),
            total_cached_tokens=total_cached if total_cached > 0 else None,
            total_cost_usd=total_cost if total_cost > 0 else None,
        )
        return self.final_metrics

    def to_dict(self, exclude_none: bool = True) -> dict[str, Any]:
        """Convert to dictionary, optionally excluding None values."""
        return self.model_dump(exclude_none=exclude_none)

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return self.model_dump_json(indent=indent, exclude_none=True)

    def to_file(self, path: str) -> None:
        """Write trajectory to a JSON file."""
        import json
        from pathlib import Path as PathLib

        PathLib(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_file(cls, path: str) -> Trajectory:
        """Load trajectory from a JSON file."""
        import json

        with open(path) as f:
            data = json.load(f)
        return cls(**data)
