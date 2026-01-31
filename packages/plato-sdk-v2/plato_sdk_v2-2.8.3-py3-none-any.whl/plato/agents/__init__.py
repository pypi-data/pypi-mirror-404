"""Plato agent framework.

Provides base classes and utilities for building and running agents.

Base Classes:
    - BaseAgent: Abstract base class for agents
    - AgentConfig: Base configuration class
    - Secret: Annotation marker for secrets

Registry:
    - register_agent: Decorator to register an agent
    - get_agent: Get an agent by name
    - get_registered_agents: Get all registered agents

Runner:
    - AgentRunner: Run agents in Docker containers
    - AgentRunResult: Async iterator for agent output

Trajectory (ATIF):
    - Trajectory: ATIF trajectory model
    - Step, Agent, ToolCall, etc.: ATIF components

OTel Tracing:
    - instrument: Initialize OTel tracing from environment
    - get_tracer: Get a tracer for creating spans

Example (direct execution):
    from plato.agents import BaseAgent, AgentConfig, Secret, register_agent
    from typing import Annotated

    class MyAgentConfig(AgentConfig):
        model_name: str = "anthropic/claude-sonnet-4"
        api_key: Annotated[str, Secret(description="API key")]

    @register_agent("my-agent")
    class MyAgent(BaseAgent[MyAgentConfig]):
        name = "my-agent"
        description = "My custom agent"

        async def run(self, instruction: str) -> None:
            # Agent implementation
            ...

Example (Docker execution):
    from plato.agents import AgentRunner

    async for line in AgentRunner.run(
        image="my-agent:latest",
        config={"model_name": "anthropic/claude-sonnet-4"},
        secrets={"api_key": "sk-..."},
        instruction="Fix the bug",
        workspace="/path/to/repo",
    ):
        print(line)
"""

from __future__ import annotations

__all__ = [
    # Config
    "AgentConfig",
    "Secret",
    # Build
    "BuildConfig",
    "load_build_config",
    # Base
    "BaseAgent",
    "ConfigT",
    "register_agent",
    "get_agent",
    "get_registered_agents",
    # Runner
    "run_agent",
    # Trajectory (ATIF)
    "Trajectory",
    "Step",
    "Agent",
    "ToolCall",
    "Observation",
    "ObservationResult",
    "Metrics",
    "FinalMetrics",
    "SCHEMA_VERSION",
    # Artifacts
    "zip_directory",
    "upload_artifacts",
    "upload_artifact",
    "upload_to_s3",
    # OTel tracing
    "init_tracing",
    "instrument",
    "shutdown_tracing",
    "get_tracer",
    "is_initialized",
]

from plato.agents.artifacts import (
    upload_artifact,
    upload_artifacts,
    upload_to_s3,
    zip_directory,
)
from plato.agents.base import (
    BaseAgent,
    ConfigT,
    get_agent,
    get_registered_agents,
    register_agent,
)
from plato.agents.build import BuildConfig, load_build_config
from plato.agents.config import AgentConfig, Secret
from plato.agents.otel import (
    get_tracer,
    init_tracing,
    instrument,
    is_initialized,
    shutdown_tracing,
)
from plato.agents.runner import run_agent
from plato.agents.trajectory import (
    SCHEMA_VERSION,
    Agent,
    FinalMetrics,
    Metrics,
    Observation,
    ObservationResult,
    Step,
    ToolCall,
    Trajectory,
)
