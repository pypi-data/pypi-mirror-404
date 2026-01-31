# Building Simulators

Internal documentation for building and snapshotting simulators.

## Snapshot Environments

Create snapshots of environment state:

```python
from plato.v2 import AsyncPlato, Env

async def main():
    plato = AsyncPlato()

    session = await plato.sessions.create(
        envs=[Env.simulator("gitea", alias="gitea")],
        timeout=600,
    )

    await session.start_heartbeat()

    # ... make changes to the environment ...

    # Snapshot all environments
    snapshots = await session.snapshot()
    print(snapshots)

    # Or snapshot individual environment
    gitea = session.get_env("gitea")
    if gitea:
        snapshot = await gitea.snapshot()
        print(snapshot)

    await session.close()
    await plato.close()
```

## Database Cleanup

Clean up database audit logs before snapshotting (async only):

```python
from plato.v2 import AsyncPlato, Env

async def main():
    plato = AsyncPlato()

    session = await plato.sessions.create(
        envs=[Env.simulator("gitea", alias="gitea")],
        timeout=600,
    )

    # ... make changes ...

    # Clean up audit logs before snapshot
    cleanup_result = await session.cleanup_databases()
    print(cleanup_result)

    # Then snapshot
    snapshots = await session.snapshot()

    await session.close()
    await plato.close()
```

Requires additional dependencies:

```bash
pip install plato-sdk-v2[db-cleanup]
```
