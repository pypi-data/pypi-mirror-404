---
name: sim-config-writer
description: Generates docker-compose.yml and plato-config.yml files for Plato simulators. Use after validation passes to create configuration files.
allowed-tools: Read, Write, Edit, Glob, Bash
context: fork
---

# Plato Simulator Config Writer

**Pipeline Position:** Phase 1, Step 3

You create the configuration files needed for a Plato simulator.

## Files You Create

```
{sim_path}/
├── plato-config.yml          # Simulator metadata and config
└── base/
    ├── docker-compose.yml    # Container orchestration
    ├── flows.yml             # Login flows (created by flow-writer)
    └── nginx.conf            # Reverse proxy (if needed)
```

## Critical Rules

### 1. Database Images - USE PLATO IMAGES

**NEVER use standard database images.** Always use Plato's signal-based images:

| Database | WRONG | CORRECT |
|----------|-------|---------|
| PostgreSQL 15 | `postgres:15` | `public.ecr.aws/i3q4i1d7/app-sim/postgres-15:prod-latest` |
| PostgreSQL 16 | `postgres:16` | `public.ecr.aws/i3q4i1d7/app-sim/postgres-16:prod-latest` |
| MySQL 8.0 | `mysql:8.0` | `public.ecr.aws/i3q4i1d7/app-sim/mysql-8.0:prod-latest` |
| MariaDB 10.6 | `mariadb:10.6` | `public.ecr.aws/i3q4i1d7/app-sim/mariadb-10.6:prod-latest` |

### 2. Network Mode

All containers MUST use `network_mode: host` for production (Plato sandbox).

### 3. Database Connection

Apps must connect to database via `127.0.0.1`, NOT the service name.

### 4. Signal-Based Healthchecks

Databases use file-based healthchecks:
```yaml
healthcheck:
  test: ["CMD-SHELL", "test -f /tmp/mysql-signals/mysql.healthy"]
  interval: 10s
  timeout: 5s
  retries: 3
  start_period: 20s
```

### 5. app_port - CRITICAL: Must Match Router's Expected Port

The router's expected port (`vm_port`) is NOT always predictable. It's usually **80 or 8888**, but you must verify by checking the public URL's routing token.

```yaml
compute:
  app_port: 80  # Start with 80, but verify!
```

**How to discover the actual port the router expects:**

```bash
# 1. Get the redirect URL
curl -sI "{public_url}" 2>&1 | grep -i location

# 2. Extract and decode the token from the location header
python3 -c "
import base64, json
token = 'PASTE_TOKEN_HERE'
token += '=' * (4 - len(token) % 4)  # Add padding
data = json.loads(base64.b64decode(token))
print(f'vm_port: {data.get(\"vm_port\")}')
"
```

**Once you know the `vm_port`:**
- Your app (or nginx) MUST listen on that port
- If app uses a different port internally, use nginx to proxy

**Example:** If `vm_port` is 80 but app listens on 8000:
```nginx
server {
    listen 80;  # Must match vm_port from routing token
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Troubleshooting 502 Bad Gateway:**

502 means nothing is listening on the port the router expects:

1. Discover `vm_port` using the steps above
2. Check what's listening: `ssh -F {ssh_config} {sandbox} "netstat -tlnp"`
3. Add nginx on `vm_port` that proxies to your app's actual port

---

## plato-config.yml Template

**IMPORTANT:** The following metadata fields are synced to the Plato server during `plato pm submit base`:
- `description` - App description
- `license` - Software license (MIT, GPL-3.0, AGPL-3.0, etc.)
- `source_code_url` - GitHub URL
- `favicon_url` - App favicon (use Google's service with the APP's domain, NOT github.com)
- `variables` with `username` and `password` - Synced as `authentication`

Make sure these are filled in correctly from the research report!

**CRITICAL for favicon_url:** Use the app's actual website domain, NOT the GitHub URL!
```yaml
# CORRECT - uses the app's website
favicon_url: "https://www.google.com/s2/favicons?domain=kimai.org&sz=32"

# WRONG - uses github.com
favicon_url: "https://www.google.com/s2/favicons?domain=github.com&sz=32"
```

```yaml
service: "{sim_name}"
datasets:
  base: &base
    compute: &base_compute
      cpus: 1          # Always 1
      memory: 2048     # Always 2048
      disk: 10240      # Always 10240
      app_port: 8888   # Router defaults to 8888!
      plato_messaging_port: 7000
    metadata: &base_metadata
      name: "{App Name}"
      description: "{Brief description of the app}"  # REQUIRED - synced to server
      source_code_url: "{github_url}"                # REQUIRED - synced to server
      favicon_url: "https://www.google.com/s2/favicons?domain={app_website}&sz=32"  # REQUIRED - use APP domain, NOT github!
      start_url: /
      license: "{license}"                           # REQUIRED - synced to server
      flows_path: base/flows.yml
      variables:                                     # REQUIRED - username/password synced as authentication
        - name: username
          value: {default_username}
        - name: password
          value: {default_password}
        - name: wrong_password
          value: wrongpassword
    services: &base_services
      main_app:
        type: docker-compose
        file: base/docker-compose.yml
        healthy_wait_timeout: 600
        required_healthy_containers:
          - {main_container_name}
    listeners: &base_listeners
      db:
        type: db
        db_type: {postgresql|mysql}
        db_host: 127.0.0.1
        db_port: {5432|3306}
        db_user: {db_user}
        db_password: {db_password}
        db_database: {db_name}
        volumes:
          - /home/plato/db_signals:/tmp/{postgres|mysql}-signals
        audit_ignore_tables:
          - sessions
          - schema_migrations
          - users: [last_login, updated_at]
```

---

## docker-compose.yml Template (PostgreSQL)

```yaml
services:
  db:
    image: public.ecr.aws/i3q4i1d7/app-sim/postgres-15:prod-latest
    network_mode: host
    environment:
      POSTGRES_USER: {db_user}
      POSTGRES_PASSWORD: {db_password}
      POSTGRES_DB: {db_name}
    volumes:
      - /home/plato/db_signals:/tmp/postgres-signals
    healthcheck:
      test: ["CMD-SHELL", "test -f /tmp/postgres-signals/postgres.healthy"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 20s

  {sim_name}-app:
    image: {docker_image}:{image_tag}
    network_mode: host
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://{db_user}:{db_password}@127.0.0.1:5432/{db_name}
      # Add other required env vars from research
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:{app_port}/ || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 5
      start_period: 45s
```

---

## docker-compose.yml Template (MySQL/MariaDB)

```yaml
services:
  db:
    image: public.ecr.aws/i3q4i1d7/app-sim/mariadb-10.6:prod-latest
    network_mode: host
    environment:
      MYSQL_DATABASE: {db_name}
      MYSQL_USER: {db_user}
      MYSQL_PASSWORD: {db_password}
      MYSQL_ROOT_PASSWORD: {db_password}
    volumes:
      - /home/plato/db_signals:/tmp/mysql-signals
    healthcheck:
      test: ["CMD-SHELL", "test -f /tmp/mysql-signals/mysql.healthy"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 20s

  {sim_name}-app:
    image: {docker_image}:{image_tag}
    network_mode: host
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: mysql://{db_user}:{db_password}@127.0.0.1:3306/{db_name}
      # Or individual vars:
      DB_HOST: 127.0.0.1
      DB_PORT: 3306
      DB_USER: {db_user}
      DB_PASSWORD: {db_password}
      DB_DATABASE: {db_name}
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:{app_port}/ || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 5
      start_period: 45s
```

---

## nginx.conf Template (REQUIRED for most apps)

**When to use:** Your app runs on port 80 but the router expects port 8888 (the default).

Nginx listens on 8888 (the router's port) and proxies to your app's actual port (usually 80):

```nginx
events {
    worker_connections 1024;
}

http {
    upstream app {
        server 127.0.0.1:80;  # Your app's actual port
    }

    server {
        listen 8888;  # Must match compute.app_port (router default is 8888)

        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
        }
    }
}
```

**Add nginx to docker-compose.yml:**
```yaml
  nginx:
    image: nginx:alpine
    network_mode: host
    depends_on:
      {sim_name}-app:
        condition: service_healthy
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8888/ || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 10s
```

**Note:** The `required_healthy_containers` in plato-config.yml should list the nginx container, not the app container, since nginx is what serves traffic on the router's port.

---

## Real Example: WordPress

**plato-config.yml:**
```yaml
service: "wordpress"
datasets:
  base: &base
    compute: &base_compute
      cpus: 1          # Always 1
      memory: 2048     # Always 2048
      disk: 10240      # Always 10240
      app_port: 8888   # Router default - nginx listens here
      plato_messaging_port: 7000
    metadata: &base_metadata
      name: "WordPress CMS"
      description: "WordPress CMS running with MariaDB in Docker"
      source_code_url: "https://github.com/WordPress/WordPress"
      start_url: /
      license: "GPL-2.0"
      flows_path: base/flows.yml
      variables:
        - name: username
          value: admin
        - name: password
          value: admin
    services: &base_services
      main_app:
        type: docker-compose
        file: base/docker-compose.yml
        healthy_wait_timeout: 600
        required_healthy_containers:
          - wordpress-nginx   # nginx, not wordpress!
    listeners: &base_listeners
      db:
        type: db
        db_type: mysql
        db_host: 127.0.0.1
        db_port: 3306
        db_user: wordpress
        db_password: wordpress
        db_database: wordpress
        volumes:
          - /home/plato/db_signals:/tmp/mysql-signals
        audit_ignore_tables:
          - wp_options
          - wp_posts: [post_modified, post_modified_gmt]
```

**docker-compose.yml:**
```yaml
services:
  db:
    image: public.ecr.aws/i3q4i1d7/app-sim/mariadb-10.6:prod-latest
    network_mode: host
    environment:
      MYSQL_DATABASE: wordpress
      MYSQL_USER: wordpress
      MYSQL_PASSWORD: wordpress
      MYSQL_ROOT_PASSWORD: wordpress
    volumes:
      - /home/plato/db_signals:/tmp/mysql-signals
    healthcheck:
      test: ["CMD-SHELL", "test -f /tmp/mysql-signals/mysql.healthy"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 20s

  wordpress:
    image: wordpress:php8.4
    network_mode: host
    depends_on:
      db:
        condition: service_healthy
    environment:
      WORDPRESS_DB_HOST: 127.0.0.1:3306
      WORDPRESS_DB_USER: wordpress
      WORDPRESS_DB_PASSWORD: wordpress
      WORDPRESS_DB_NAME: wordpress
      WORDPRESS_CONFIG_EXTRA: |
        define('WP_HOME', 'https://sims.plato.so');
        define('WP_SITEURL', 'https://sims.plato.so');
        define('FORCE_SSL_ADMIN', true);
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:80/ || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 5
      start_period: 45s

  wordpress-nginx:
    image: nginx:alpine
    network_mode: host
    depends_on:
      wordpress:
        condition: service_healthy
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8888/ || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 10s
```

**nginx.conf:**
```nginx
events { worker_connections 1024; }
http {
    server {
        listen 8888;
        location / {
            proxy_pass http://127.0.0.1:80;
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-Proto https;
        }
    }
}
```

---

## Common audit_ignore_tables

Add these to prevent false mutations:

```yaml
audit_ignore_tables:
  # Framework tables (ignore entirely)
  - sessions
  - schema_migrations
  - ar_internal_metadata
  - django_migrations
  - doctrine_migration_versions

  # Column-level ignores (inline format - PREFERRED)
  - users: [last_login, updated_at, session_token]
  - posts: [view_count, modified_at]
```

### audit_ignore_tables Formats

**Format 1: Ignore entire table**
```yaml
audit_ignore_tables:
  - sessions           # Ignores ALL changes to this table
```

**Format 2: Ignore specific columns (inline - PREFERRED)**
```yaml
audit_ignore_tables:
  - users: [last_login, updated_at]  # Only ignore these columns on UPDATE
  - kimai2_users: [last_login, totp_secret]
```

**Format 3: Ignore specific columns (verbose)**
```yaml
audit_ignore_tables:
  - table: users
    columns: [last_login, updated_at]
```

**IMPORTANT:** Do NOT use a separate `ignore_columns` field. Column-level ignores must be inside `audit_ignore_tables`.

---

## Output

After creating files:
```
Config files created at {sim_path}/:
- plato-config.yml
- base/docker-compose.yml
- base/nginx.conf (if needed)

Next: Use sim-sandbox-operator to start sandbox and services.
```

---

## Real Example: Corteza (Go app, Single Container)

Corteza is a low-code platform. Simple setup: one app container + PostgreSQL.

**plato-config.yml:**
```yaml
service: "corteza"
datasets:
  base: &base
    compute: &base_compute
      cpus: 2
      memory: 4096
      disk: 10240
      app_port: 80
      plato_messaging_port: 7000
    metadata: &base_metadata
      name: "Corteza Server Simulation"
      description: "Low-code platform for building CRM and business process applications"
      source_code_url: "https://github.com/cortezaproject/corteza"
      start_url: /auth
      license: "Apache-2.0"
      flows_path: base/flows.yml
      variables:
        - name: db_url
          value: postgres://corteza:corteza@127.0.0.1:5432/corteza?sslmode=disable
        - name: app_base_url
          value: https://sims.plato.so
    services: &base_services
      main_app:
        type: docker-compose
        file: base/docker-compose.yml
        healthy_wait_timeout: 600
        required_healthy_containers:
          - corteza
    listeners: &base_listeners
      db:
        type: db
        db_type: postgresql
        db_host: 127.0.0.1
        db_port: 5432
        db_user: corteza
        db_password: corteza
        db_database: corteza
        volumes:
          - /home/plato/db_signals:/tmp/postgres-signals
        audit_ignore_tables:
          - actionlog
          - auth_sessions
          - users: [created_at, updated_at, deleted_at]
```

**docker-compose.yml:**
```yaml
services:
  db:
    platform: linux/amd64
    image: public.ecr.aws/i3q4i1d7/app-sim/postgres-17-alpine:prod-latest
    network_mode: host
    command: ["postgres", "-c", "listen_addresses=127.0.0.1"]
    environment:
      POSTGRES_USER: corteza
      POSTGRES_DB: corteza
      POSTGRES_PASSWORD: corteza
    volumes:
      - /home/plato/db_signals:/tmp/postgres-signals
    healthcheck:
      test:
        - CMD-SHELL
        - ls -la /tmp/postgres-signals/ && test -f /tmp/postgres-signals/pg.healthy && echo 'Health check passed'
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  corteza:
    platform: linux/amd64
    image: cortezaproject/corteza:2024.9
    network_mode: host
    depends_on:
      db:
        condition: service_healthy
    extra_hosts:
        - "host.docker.internal:127.0.0.1"
    environment:
      DB_DSN: postgres://corteza:corteza@127.0.0.1:5432/corteza?sslmode=disable
      DOMAIN: "sims.plato.so"
      DOMAIN_WEBAPP: ""
      HTTP_ADDR: 0.0.0.0:80
      HTTP_SSL_TERMINATED: "true"
      HTTP_WEBAPP_ENABLED: "true"
      HTTP_WEBAPP_BASE_URL: /
      HTTP_API_BASE_URL: /api
      ACTIONLOG_ENABLED: "false"
      AUTH_JWT_SECRET: plato-corteza-secret-key-minimum-30-chars-long
      AUTH_EXTERNAL_ENABLED: "false"
      PROVISION_ALWAYS: "true"
    healthcheck:
      test: ["CMD", "curl", "--silent", "--fail", "--fail-early", "http://127.0.0.1:80/healthcheck"]
      interval: 30s
      timeout: 30s
      retries: 5
      start_period: 120s
```

**Key patterns:**
- App listens on port 80 directly (no nginx needed)
- `HTTP_SSL_TERMINATED: "true"` - app is behind HTTPS proxy
- `DOMAIN` and `DOMAIN_WEBAPP` set for Plato's routing
- `PROVISION_ALWAYS: "true"` - auto-creates admin user
- `ACTIONLOG_ENABLED: "false"` - reduces noise
- audit_ignore: `actionlog`, `auth_sessions`, timestamp columns

---

## Real Example: Worklenz (Node.js, Multi-Container)

Worklenz is a project management tool. Complex setup: frontend + backend + nginx + minio + PostgreSQL.

**plato-config.yml:**
```yaml
service: worklenz
datasets:
  base: &base
    compute: &base_compute
      cpus: 1
      memory: 2048
      disk: 10240
      app_port: 80
      plato_messaging_port: 7000
    metadata: &base_metadata
      name: Worklenz
      description: All-in-one project management tool with task management, time tracking, analytics, and team collaboration
      source_code_url: https://github.com/Worklenz/worklenz
      start_url: blank
      license: AGPL-3.0
      variables:
        - name: username
          value: admin@admin.com
        - name: password
          value: Admin123!
        - name: wrong_password
          value: wrongpassword
      flows_path: login-flow.yml
    services: &base_services
      main_app:
        type: docker-compose
        file: base/docker-compose.yml
        healthy_wait_timeout: 600
        required_healthy_containers:
          - worklenz_frontend
    listeners: &base_listeners
      db:
        type: db
        db_type: postgresql
        db_host: 127.0.0.1
        db_port: 5432
        db_user: worklenz
        db_password: worklenz
        db_database: worklenz_db
        volumes:
          - /home/plato/db_signals:/tmp/postgres-signals
        audit_ignore_tables:
          - users: [created_at, updated_at]
          - projects: [created_at, updated_at]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  db:
    image: public.ecr.aws/i3q4i1d7/app-sim/postgres-15-alpine:prod-latest
    container_name: worklenz_db
    network_mode: host
    environment:
      POSTGRES_DB: worklenz_db
      POSTGRES_USER: worklenz
      POSTGRES_PASSWORD: worklenz
      POSTGRES_ROOT_PASSWORD: worklenz
    volumes:
      - /home/plato/db_signals:/tmp/postgres-signals
      - ./worklenz/worklenz-backend/database/sql:/docker-entrypoint-initdb.d/sql
      - ./worklenz/worklenz-backend/database/migrations:/docker-entrypoint-initdb.d/migrations
      - ./worklenz/worklenz-backend/database/00_init.sh:/docker-entrypoint-initdb.d/00_init.sh
    healthcheck:
      test: [ "CMD-SHELL", "ls -la /tmp/postgres-signals/ && test -f /tmp/postgres-signals/pg.healthy && echo 'Health check passed'" ]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s
    restart: unless-stopped

  minio:
    image: minio/minio:latest
    container_name: worklenz_minio
    network_mode: host
    environment:
      MINIO_ROOT_USER: worklenz_minio_admin
      MINIO_ROOT_PASSWORD: worklenz_minio_secure_2024
      MINIO_ADDRESS: :9000
      MINIO_CONSOLE_ADDRESS: :9001
    volumes:
      - ./minio_data:/data
    command: server /data --console-address ":9001"
    restart: unless-stopped

  backend:
    image: awmckinn/worklenz-backend:prod-latest
    container_name: worklenz_backend
    network_mode: host
    depends_on:
      db:
        condition: service_healthy
      minio:
        condition: service_started
    environment:
      SERVER_CORS: "https://sims.plato.so"
      SOCKET_IO_CORS: "https://sims.plato.so"
      FRONTEND_URL: "https://sims.plato.so"
      HOSTNAME: "sims.plato.so"
      DB_HOST: 127.0.0.1
      DB_PORT: 5432
      DB_USER: worklenz
      DB_PASSWORD: worklenz
      DB_NAME: worklenz_db
      AWS_REGION: us-east-1
      AWS_BUCKET: worklenz-bucket
      S3_URL: http://127.0.0.1:9000/worklenz-bucket
      AWS_ACCESS_KEY_ID: worklenz_minio_admin
      AWS_SECRET_ACCESS_KEY: worklenz_minio_secure_2024
      PORT: 3000
      NODE_ENV: production
      SESSION_SECRET: worklenz_session_secret_change_in_production
      GOOGLE_CLIENT_ID: dummy_client_id
      GOOGLE_CLIENT_SECRET: dummy_client_secret
      GOOGLE_CALLBACK_URL: https://sims.plato.so/auth/google/callback
      SLACK_WEBHOOK: "https://httpbin.org/post"
      TEAMS_SUPPORT_WEBHOOK: "https://httpbin.org/post"
    restart: unless-stopped

  frontend:
    image: awmckinn/worklenz-frontend:prod-latest
    container_name: worklenz_frontend
    network_mode: host
    depends_on:
      - backend
    environment:
      VITE_API_URL: "/api"
      VITE_SOCKET_URL: "https://sims.plato.so"
      PORT: 5000
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: worklenz_nginx
    network_mode: host
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
```

**nginx/nginx.conf:**
```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server 127.0.0.1:3000;
    }

    upstream frontend {
        server 127.0.0.1:5000;
    }

    server {
        listen 80;

        # Backend API routes
        location /api/ {
            proxy_pass http://backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /secure/ {
            proxy_pass http://backend/secure/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /socket/ {
            proxy_pass http://127.0.0.1:3000/socket/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        # Frontend - everything else
        location / {
            proxy_pass http://frontend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

**Key patterns:**
- nginx on port 80 routes to frontend (5000) and backend (3000)
- WebSocket support for `/socket/` with upgrade headers
- MinIO for S3-compatible storage (common pattern)
- CORS and frontend URLs all point to `sims.plato.so`
- Database init scripts mounted to `/docker-entrypoint-initdb.d/`
- Simple audit_ignore: just timestamp columns

---

## DO NOT

- Use standard database images (postgres:15, mysql:8.0, etc.)
- Use service names for database connections (use 127.0.0.1)
- Forget `network_mode: host`
- Forget the db_signals volume mount
- Use `latest` tag for app images
