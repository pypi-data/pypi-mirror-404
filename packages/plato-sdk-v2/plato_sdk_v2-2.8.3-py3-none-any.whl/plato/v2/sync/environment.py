"""Plato SDK v2 - Synchronous Environment."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from plato._generated.api.v2 import jobs
from plato._generated.models import (
    AppApiV2SchemasSessionCreateSnapshotRequest,
    CreateCheckpointRequest,
    CreateSnapshotResult,
    ExecuteCommandRequest,
    ExecuteCommandResult,
    ResetJobResult,
    ResetSessionRequest,
    SessionStateResult,
    SetDateRequest,
    SetDateResult,
)

if TYPE_CHECKING:
    from plato.v2.sync.session import Session


class Environment:
    """An environment represents a single VM within a session.

    Usage:
        with client.session(envs=[EnvOption(simulator="espocrm")]) as session:
            for env in session.envs:
                state = env.get_state()
                result = env.execute("ls -la")
    """

    def __init__(
        self,
        session: Session,
        job_id: str,
        alias: str,
        artifact_id: str | None = None,
    ):
        self._session = session
        self.job_id = job_id
        self.alias = alias
        self.artifact_id = artifact_id

    @property
    def _http(self):
        """Access the HTTP client from the session."""
        return self._session._http

    @property
    def _api_key(self) -> str:
        """Access the API key from the session."""
        return self._session._api_key

    @property
    def session_id(self) -> str:
        return self._session.session_id

    def reset(self, **kwargs) -> ResetJobResult:
        """Reset this environment to initial state."""
        request = ResetSessionRequest(**kwargs)
        return jobs.reset.sync(
            client=self._http,
            job_id=self.job_id,
            body=request,
            x_api_key=self._api_key,
        )

    def get_state(self) -> SessionStateResult:
        """Get state from this environment."""
        return jobs.state.sync(
            client=self._http,
            job_id=self.job_id,
            x_api_key=self._api_key,
        )

    def execute(
        self,
        command: str,
        timeout: int = 30,
    ) -> ExecuteCommandResult:
        """Execute a command on this environment.

        Args:
            command: Shell command to execute.
            timeout: Command timeout in seconds.

        Returns:
            Execution result with stdout, stderr, exit_code.
        """
        request = ExecuteCommandRequest(
            command=command,
            timeout=timeout,
        )
        return jobs.execute.sync(
            client=self._http,
            job_id=self.job_id,
            body=request,
            x_api_key=self._api_key,
        )

    def set_date(
        self,
        dt: datetime,
        timeout: int = 30,
    ) -> SetDateResult:
        """Set the system date on this environment.

        Args:
            dt: The datetime to set.
            timeout: Command timeout in seconds.

        Returns:
            SetDateResult with success status and command output.
        """
        request = SetDateRequest(
            datetime=dt.isoformat(),
            timeout=timeout,
        )
        return jobs.set_date.sync(
            client=self._http,
            job_id=self.job_id,
            body=request,
            x_api_key=self._api_key,
        )

    def snapshot(self) -> CreateSnapshotResult:
        """Create a snapshot of this environment."""
        return jobs.snapshot.sync(
            client=self._http,
            job_id=self.job_id,
            body=CreateCheckpointRequest(),
            x_api_key=self._api_key,
        )

    def snapshot_store(
        self,
        override_service: str | None = None,
        override_version: str | None = None,
        override_dataset: str | None = None,
    ) -> CreateSnapshotResult:
        """Create a snapshot-store snapshot of this environment.

        Uses the snapshot-store pipeline for chunk-based deduplication and
        efficient storage. This is the preferred method for new base snapshots.

        Args:
            override_service: Override simulator/service name in artifact metadata.
            override_version: Override version/git_hash in artifact metadata.
            override_dataset: Override dataset name in artifact metadata.

        Returns:
            CreateSnapshotResult with artifact_id.
        """
        return jobs.snapshot_store.sync(
            client=self._http,
            job_id=self.job_id,
            body=AppApiV2SchemasSessionCreateSnapshotRequest(
                override_service=override_service,
                override_version=override_version,
                override_dataset=override_dataset,
            ),
            x_api_key=self._api_key,
        )

    def close(self) -> None:
        """Close this environment."""
        jobs.close.sync(
            client=self._http,
            job_id=self.job_id,
            x_api_key=self._api_key,
        )

    def __repr__(self) -> str:
        return f"Environment(alias={self.alias!r}, job_id={self.job_id!r})"
