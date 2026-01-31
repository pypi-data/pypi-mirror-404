# World runner image for plato chronos dev
# Includes git, docker CLI, and Python dependencies

FROM python:3.12-slim

# Install git and docker CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && curl -fsSL https://get.docker.com -o get-docker.sh \
    && sh get-docker.sh \
    && rm get-docker.sh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package installation
RUN pip install --no-cache-dir uv

WORKDIR /world

# Entry point expects:
# - /world mounted with world source
# - /python-sdk mounted with plato SDK source (optional, for dev)
# - /config.json mounted with config
# - WORLD_NAME env var set
CMD ["bash", "-c", "if [ -d /python-sdk ]; then uv pip install --system /python-sdk; fi && uv pip install --system . 2>/dev/null || pip install -q . && plato-world-runner run --world $WORLD_NAME --config /config.json"]
