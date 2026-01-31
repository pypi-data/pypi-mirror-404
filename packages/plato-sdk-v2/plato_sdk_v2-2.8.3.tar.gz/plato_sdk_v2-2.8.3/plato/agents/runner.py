"""Agent runner - run agents in Docker containers.

Agents emit their own OTel spans for trajectory events. This runner:
1. Runs agents in Docker containers
2. Streams stdout/stderr for logging
3. Passes OTel environment variables for trace context propagation
4. Uploads artifacts to S3 when complete
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import platform
import uuid

from opentelemetry import trace

logger = logging.getLogger(__name__)


async def run_agent(
    image: str,
    config: dict,
    instruction: str,
    workspace: str | None = None,
    logs_dir: str | None = None,
    pull: bool = True,
) -> str:
    """Run an agent in a Docker container.

    Args:
        image: Docker image URI
        config: Agent configuration dict (includes secrets)
        instruction: Task instruction for the agent
        workspace: Docker volume name for workspace (created if None)
        logs_dir: Ignored (kept for backwards compatibility)
        pull: Whether to pull the image first

    Returns:
        The container name that was created (for cleanup purposes)

    Note: Agents handle their own OTel tracing. This runner only passes
    the trace context (TRACEPARENT) so agent spans link to the parent step.

    Note: This uses Docker volumes (not bind mounts) for DIND compatibility.
    The workspace parameter should be a Docker volume name.
    """
    # Get session info from environment variables
    session_id = os.environ.get("SESSION_ID")
    otel_url = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    upload_url = os.environ.get("UPLOAD_URL")

    # Pull image if requested
    if pull:
        pull_proc = await asyncio.create_subprocess_exec(
            "docker",
            "pull",
            image,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        await pull_proc.wait()

    # Encode config as base64 to pass via environment variable
    # This avoids file mount issues in Docker-in-Docker scenarios
    config_json = json.dumps(config)
    config_b64 = base64.b64encode(config_json.encode()).decode()

    # Generate a unique container name for inspection
    container_name = f"agent-{uuid.uuid4().hex[:8]}"

    # Use WORKSPACE_VOLUME env var if set (for DIND compatibility)
    # Otherwise create a new volume
    workspace_volume = os.environ.get("WORKSPACE_VOLUME") or workspace or f"workspace-{uuid.uuid4().hex[:8]}"
    if not os.environ.get("WORKSPACE_VOLUME") and not workspace:
        await asyncio.create_subprocess_exec(
            "docker",
            "volume",
            "create",
            workspace_volume,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )

    # Create logs volume
    logs_volume = f"logs-{uuid.uuid4().hex[:8]}"
    await asyncio.create_subprocess_exec(
        "docker",
        "volume",
        "create",
        logs_volume,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )

    try:
        # Build docker command
        docker_cmd = ["docker", "run", "--rm", "--privileged", "--name", container_name]

        # Determine if we need host networking
        use_host_network = False
        is_macos = platform.system() == "Darwin"

        if not is_macos:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "iptables",
                    "-L",
                    "-n",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await proc.wait()
                has_iptables = proc.returncode == 0
            except (FileNotFoundError, PermissionError):
                has_iptables = False

            use_host_network = not has_iptables

        if use_host_network:
            docker_cmd.extend(["--network=host", "--add-host=localhost:127.0.0.1"])

        # Use Docker volumes instead of bind mounts for DIND compatibility
        docker_cmd.extend(
            [
                "-v",
                f"{workspace_volume}:/workspace",
                "-v",
                f"{logs_volume}:/logs",
                "-v",
                "/var/run/docker.sock:/var/run/docker.sock",
                "-w",
                "/workspace",
                "-e",
                f"AGENT_CONFIG_B64={config_b64}",
            ]
        )

        # Pass session info to agent
        if otel_url:
            traces_endpoint = f"{otel_url.rstrip('/')}/v1/traces"
            docker_cmd.extend(["-e", f"OTEL_EXPORTER_OTLP_ENDPOINT={otel_url}"])
            docker_cmd.extend(["-e", f"OTEL_EXPORTER_OTLP_TRACES_ENDPOINT={traces_endpoint}"])
            docker_cmd.extend(["-e", "OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf"])
        if session_id:
            docker_cmd.extend(["-e", f"SESSION_ID={session_id}"])
        if upload_url:
            docker_cmd.extend(["-e", f"UPLOAD_URL={upload_url}"])

        # Pass trace context to agent for parent linking
        # Agent spans will be children of the current step span
        current_span = trace.get_current_span()
        span_context = current_span.get_span_context()
        if span_context.is_valid:
            trace_id = format(span_context.trace_id, "032x")
            span_id = format(span_context.span_id, "016x")
            # W3C Trace Context format for TRACEPARENT
            traceparent = f"00-{trace_id}-{span_id}-01"
            docker_cmd.extend(
                [
                    "-e",
                    f"TRACEPARENT={traceparent}",
                    "-e",
                    f"OTEL_TRACE_ID={trace_id}",
                    "-e",
                    f"OTEL_PARENT_SPAN_ID={span_id}",
                ]
            )

        docker_cmd.append(image)

        # Pass instruction via CLI arg
        docker_cmd.extend(["--instruction", instruction])

        logger.debug(f"Starting container: {container_name}")

        # Run container - agents emit their own OTel spans
        # Use large limit to handle agents that output long lines (e.g., JSON with file contents)
        process = await asyncio.create_subprocess_exec(
            *docker_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            limit=100 * 1024 * 1024,  # 100MB buffer limit
        )

        # Stream and capture output for error reporting using chunked reads to handle large lines
        output_lines: list[str] = []
        assert process.stdout is not None
        buffer = ""
        while True:
            try:
                chunk = await process.stdout.read(65536)
            except Exception:
                break
            if not chunk:
                break
            buffer += chunk.decode(errors="replace")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                output_lines.append(line)
                # Print agent output in real-time
                print(f"[agent] {line}")

        # Handle any remaining content in buffer
        if buffer.strip():
            output_lines.append(buffer)
            print(f"[agent] {buffer}")

        await process.wait()

        exit_code = process.returncode or 0
        if exit_code != 0:
            error_context = "\n".join(output_lines[-50:]) if output_lines else "No output captured"
            raise RuntimeError(f"Agent failed with exit code {exit_code}\n\nAgent output:\n{error_context}")

    finally:
        # Clean up volumes
        await asyncio.create_subprocess_exec(
            "docker",
            "volume",
            "rm",
            "-f",
            logs_volume,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        # Note: workspace_volume is not cleaned up as it may be shared

    return container_name
