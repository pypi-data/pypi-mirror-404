"""Helper types for Plato SDK v2.

Re-exports generated models and provides ergonomic factory methods.
"""

from __future__ import annotations

from typing import Any

from plato._generated.models import (
    AppSchemasBuildModelsSimConfigCompute as SimConfigCompute,
)
from plato._generated.models import (
    EnvFromArtifact,
    EnvFromResource,
    EnvFromSimulator,
)


class Env:
    """Factory for environment configurations.

    Provides ergonomic builder methods for environment modes:
    1. simulator + tag: Env.simulator("env:tag") - from artifact snapshot
    2. artifact_id: Env.artifact("artifact-123") - from explicit artifact
    3. simulator + sim_config: Env.resource(...) - blank VM with custom resources
    """

    @staticmethod
    def simulator(
        simulator: str,
        *,
        tag: str = "latest",
        dataset: str | None = None,
        alias: str | None = None,
    ) -> EnvFromSimulator:
        """Create env from simulator with tag.

        Args:
            simulator: Simulator name, or "env:tag" format (e.g., "espocrm:staging")
            tag: Artifact tag (default: "latest"). Ignored if simulator contains ":"
            dataset: Dataset name (e.g., "base", "blank"). If not specified, uses default.
            alias: Custom name for this environment

        Returns:
            EnvFromSimulator

        Examples:
            >>> Env.simulator("espocrm")  # -> uses "latest" tag
            >>> Env.simulator("espocrm:staging")  # -> uses "staging" tag
            >>> Env.simulator("espocrm", tag="staging")  # -> uses "staging" tag
            >>> Env.simulator("gitea", dataset="blank")  # -> uses "blank" dataset
        """
        # Support "env:tag" format
        if ":" in simulator:
            sim_name, tag = simulator.split(":", 1)
        else:
            sim_name = simulator

        # Build kwargs, only including dataset if specified
        kwargs: dict[str, Any] = {
            "simulator": sim_name,
            "tag": tag,
            "alias": alias,
        }
        if dataset is not None:
            kwargs["dataset"] = dataset

        return EnvFromSimulator(**kwargs)

    @staticmethod
    def artifact(
        artifact_id: str,
        *,
        alias: str | None = None,
    ) -> EnvFromArtifact:
        """Create env from explicit artifact ID.

        Args:
            artifact_id: Specific artifact/snapshot ID to use
            alias: Custom name for this environment

        Returns:
            EnvFromArtifact

        Example:
            >>> Env.artifact("artifact-123")
        """
        return EnvFromArtifact(
            artifact_id=artifact_id,
            alias=alias,
        )

    @staticmethod
    def resource(
        simulator: str,
        sim_config: SimConfigCompute,
        *,
        alias: str | None = None,
    ) -> EnvFromResource:
        """Create env from resource specification (blank VM).

        Args:
            simulator: Simulator/service name
            sim_config: Resource configuration (CPUs, memory, disk)
            alias: Custom name for this environment

        Returns:
            EnvFromResource

        Example:
            >>> Env.resource("redis", SimConfigCompute(cpus=4, memory=8192, disk=20000))
        """
        return EnvFromResource(
            simulator=simulator,
            sim_config=sim_config,
            alias=alias,
        )


__all__ = [
    "Env",
    "EnvFromSimulator",
    "EnvFromArtifact",
    "EnvFromResource",
    "SimConfigCompute",
]
