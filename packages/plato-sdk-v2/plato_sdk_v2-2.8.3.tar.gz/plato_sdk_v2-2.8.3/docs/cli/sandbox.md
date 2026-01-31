# plato sandbox

Manage sandbox environments for simulator development. Sandboxes are ephemeral VMs where you can develop, test, and iterate on simulators.

## Commands

| Command | Description |
|---------|-------------|
| `start` | Start a new sandbox environment |
| `stop` | Stop and destroy the sandbox |
| `status` | Show current sandbox status |
| `sync` | Sync local code to the sandbox |
| `snapshot` | Create a snapshot (artifact) of current state |
| `flow` | Execute a test flow against the simulator |
| `start-worker` | Start/configure the Plato worker |
| `start-services` | Push code and start docker compose services |
| `state` | Get the current state of the environment |
| `audit-ui` | Launch Streamlit UI for auditing database ignore rules |

## plato sandbox start

Start a sandbox environment. Three modes available:

### Mode 1: From Config (Development)

Use `plato-config.yml` in the current directory. Creates a blank VM with specs from config.

```bash
# Use default dataset
plato sandbox start --from-config

# Specify dataset
plato sandbox start --from-config --dataset base
```

### Mode 2: From Artifact/Simulator (Testing)

Start from a published simulator or artifact ID.

```bash
# From simulator name
plato sandbox start --simulator espocrm
plato sandbox start --simulator espocrm:prod-latest

# From specific artifact
plato sandbox start --artifact-id art_abc123
```

### Mode 3: Blank VM (Custom)

Create a fresh VM with custom specs.

```bash
plato sandbox start --blank --service myapp
plato sandbox start --blank --service myapp --cpus 4 --memory 2048 --disk 20480
```

### Options

| Option | Description |
|--------|-------------|
| `--from-config, -c` | Use plato-config.yml in current directory |
| `--simulator, -s` | Simulator name (e.g., espocrm, espocrm:staging) |
| `--artifact-id, -a` | Specific artifact ID |
| `--blank, -b` | Create blank VM |
| `--dataset, -d` | Dataset from config or simulator |
| `--tag, -t` | Artifact tag (default: latest) |
| `--service` | Service name (required for blank VM) |
| `--cpus` | Number of CPUs (default: 2) |
| `--memory` | Memory in MB (default: 1024) |
| `--disk` | Disk in MB (default: 10240) |
| `--timeout` | Timeout for VM ready in seconds (default: 300) |
| `--no-reset` | Skip initial reset after ready |
| `--json, -j` | Output as JSON |

## plato sandbox stop

Stop and destroy the current sandbox. Cleans up SSH keys and removes `.sandbox.yaml`.

```bash
plato sandbox stop
```

## plato sandbox status

Show current sandbox status including VM health, SSH command, and heartbeat status.

```bash
plato sandbox status
plato sandbox status --json
```

Example output:
```
Sandbox Status
  Session ID:  abc123-def456
  Job ID:      job-789
  Mode:        config
  VM Status:   active
  Service:     docuseal
  Public URL:  https://job-789.sims.plato.so?_plato_router_target=docuseal.web.plato.so
  SSH:         ssh -F ~/.plato/ssh_abc123.conf sandbox-abc123
  Heartbeat:   running (PID: 1234)
```

## plato sandbox sync

Sync local code to the sandbox. Creates a tar archive, uploads via API, and extracts on the VM.

```bash
# Sync current directory
plato sandbox sync

# Sync specific path
plato sandbox sync ./src

# Sync to custom remote path
plato sandbox sync --remote-path /home/plato/custom/path
```

### Excluded Patterns

The following are automatically excluded:
- `__pycache__`, `*.pyc`
- `.git`, `.venv`, `venv`, `node_modules`
- `.sandbox.yaml`, `*.egg-info`
- `.pytest_cache`, `.mypy_cache`
- `.DS_Store`, `*.swp`, `*.swo`

## plato sandbox snapshot

Create a snapshot (artifact) of the current sandbox state.

```bash
plato sandbox snapshot
plato sandbox snapshot --json
```

Output:
```
Snapshot created successfully!
  Artifact ID: art_xyz789
```

## plato sandbox flow

Execute a test flow against the simulator environment. Uses Playwright to run browser automation.

```bash
# Run default login flow
plato sandbox flow

# Run specific flow
plato sandbox flow --flow-name checkout
```

### Flow Source Priority

1. **Local plato-config.yml** - If a local config exists with `metadata.flows_path`, uses local flows (development workflow)
2. **API fallback** - If no local config, fetches flows from the artifact via API (testing published artifacts)

### Options

| Option | Description |
|--------|-------------|
| `--flow-name, -f` | Name of the flow to execute (default: login) |

## plato sandbox start-worker

Start/configure the Plato worker in the sandbox. Required after creating a blank VM.

```bash
# Use config in current directory
plato sandbox start-worker

# Specify config path
plato sandbox start-worker --config-path ./plato-config.yml

# Override service and dataset
plato sandbox start-worker -s myapp -d base
```

### Options

| Option | Description |
|--------|-------------|
| `--service, -s` | Service name (uses sandbox service if not specified) |
| `--dataset, -d` | Dataset name (default: base) |
| `--config-path` | Path to plato-config.yml |
| `--json, -j` | Output as JSON |

## plato sandbox start-services

Push local code to Plato Hub, clone on VM, and start docker compose services.

```bash
plato sandbox start-services
plato sandbox start-services --json
```

This command:
1. Gets Gitea credentials
2. Finds/creates simulator repository
3. Pushes local code to a workspace branch
4. Clones the branch on the VM
5. Starts docker compose services defined in plato-config.yml

## plato sandbox state

Get the current state of the simulator environment (database state, mutations, etc.).

```bash
plato sandbox state
```

## plato sandbox audit-ui

Launch Streamlit UI for auditing database ignore rules.

```bash
plato sandbox audit-ui
```

Requires: `pip install streamlit psycopg2-binary pymysql`

## State File (.sandbox.yaml)

The sandbox state is persisted to `.sandbox.yaml` in the current directory. This file contains:

```yaml
session_id: abc123-def456
job_id: job-789
public_url: https://job-789.sims.plato.so
url: https://job-789.sims.plato.so?_plato_router_target=service.web.plato.so
mode: config
service: docuseal
dataset: base
plato_config_path: /path/to/plato-config.yml
ssh_host: sandbox-abc123
ssh_config_path: ~/.plato/ssh_abc123.conf
heartbeat_pid: 1234
created_at: 2024-01-01T00:00:00+00:00
```

## SSH Access

After starting a sandbox with `--from-config`, SSH access is automatically configured:

```bash
# SSH command shown in status
ssh -F ~/.plato/ssh_abc123.conf sandbox-abc123

# Run docker commands
ssh -F ~/.plato/ssh_abc123.conf sandbox-abc123 "docker ps"

# Access worktree
ssh -F ~/.plato/ssh_abc123.conf sandbox-abc123 "ls /home/plato/worktree/service/"
```

## Heartbeat (Background Process)

Sandboxes require periodic heartbeats to stay alive. When you run `plato sandbox start`, a **background Python process** is automatically spawned that sends heartbeats to the Plato API every 30 seconds.

### How It Works

1. **On `sandbox start`**: A detached Python process is spawned using `subprocess.Popen` with `start_new_session=True`
2. **The process**: Runs independently of the CLI, sending POST requests to `/api/v2/sessions/{session_id}/heartbeat`
3. **PID tracking**: The process ID is saved to `.sandbox.yaml` as `heartbeat_pid`
4. **On `sandbox stop`**: The process is terminated via `SIGTERM`

### Why This Matters

- **Without heartbeats**: VMs are automatically shut down after ~2 minutes of inactivity
- **Background process**: Allows you to close the terminal and keep the sandbox running
- **Persistent development**: You can SSH into the sandbox, work, and come back later

### Monitoring

Check heartbeat status with `plato sandbox status`:

```
Heartbeat:   running (PID: 1234)    # Process is alive
Heartbeat:   stopped (PID: 1234 not found)  # Process died
```

### Manual Management

If the heartbeat process dies but you want to keep the sandbox:

```bash
# Check if process is running
ps aux | grep "heartbeat"

# Manually kill if needed
kill <pid>
```

### Troubleshooting

**"VM shutdown due to heartbeat miss"**

This means the heartbeat process stopped or failed. Causes:
- Process was killed manually
- System Python doesn't have `httpx` installed
- Network issues preventing API calls

**Solution**: Start a fresh sandbox with `plato sandbox stop && plato sandbox start ...`

### Technical Details

The heartbeat process runs this script:

```python
import time, httpx
while True:
    httpx.Client().post(f"/api/v2/sessions/{session_id}/heartbeat", ...)
    time.sleep(30)
```

It uses the system Python (`python3`) and requires `httpx` to be available.

## See Also

- [Creating Flows](flows.md) - How to write login and test flows
- [Simulator Lifecycle Guide](../SIMULATOR_LIFECYCLE.md) - Complete workflow for building simulators
- [Main CLI Reference](../CLI.md) - Overview of all CLI commands
