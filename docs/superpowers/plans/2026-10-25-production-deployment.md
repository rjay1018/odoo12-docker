# Production Deployment Alongside Staging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Configure and deploy a dedicated, isolated Odoo 12 production instance (`odoo-web-prod`) running alongside the existing staging instance on the same Ubuntu 24.04 server.

**Architecture:** A parallel configuration architecture where production has dedicated compose definitions (`docker-compose.prod.yml`), dedicated config (`odoo.prod.conf`), isolated filestore volumes (`odoo_odoo-web-prod-data`), isolated database (`yyy_prod` on host PostgreSQL 16), and an independent deployment script (`deploy-prod.sh`), sharing the global `nginx-proxy` and host UNIX domain socket.

**Tech Stack:** Docker, Docker Compose, Odoo 12, Python 3.8, PostgreSQL 16, Nginx, Let's Encrypt / acme-companion, Bash.

## Global Constraints

- Container name for production must be `odoo-web-prod`
- Domain name for production must be `yyy.on-cloud.io`
- Local host port binding must be `127.0.0.1:8079:8069` to prevent port collision with staging (`8069`)
- Named Docker volume for production filestore must be `odoo_odoo-web-prod-data`
- Production database must be `yyy_prod` on host PostgreSQL 16 via `/var/run/postgresql` socket
- Strict database isolation must be enforced via `db_name = yyy_prod`, `dbfilter = ^yyy_prod$`, and `list_db = False`
- Staging container `odoo-web` and volumes must remain completely untouched during production deployment

---

### Task 1: Create Production Odoo Configuration (`odoo/config/odoo.prod.conf`)

**Files:**
- Create: `odoo/config/odoo.prod.conf`
- Test: `tests/test_configs.py`

**Interfaces:**
- Consumes: Specifications from `docs/superpowers/specs/2026-10-25-production-deployment-design.md`
- Produces: Production Odoo configuration file mounted to `/etc/odoo/odoo.conf` inside `odoo-web-prod`

- [ ] **Step 1: Write configuration validator test**

Create a test script `tests/test_configs.py` that verifies that `odoo/config/odoo.prod.conf` contains all required production directives (`dbfilter`, `db_name`, `list_db`, memory limits, etc.):

```python
import os
import configparser

def test_odoo_prod_conf():
    conf_path = os.path.join(os.path.dirname(__file__), "..", "odoo", "config", "odoo.prod.conf")
    assert os.path.exists(conf_path), f"Configuration file not found: {conf_path}"
    
    config = configparser.ConfigParser()
    config.read(conf_path)
    
    options = config["options"]
    assert options.get("db_name") == "yyy_prod", "db_name must be yyy_prod"
    assert options.get("dbfilter") == "^yyy_prod$", "dbfilter must be ^yyy_prod$"
    assert options.get("list_db") == "False", "list_db must be False"
    assert options.get("db_host") == "False", "db_host must be False for UNIX socket"
    assert options.get("db_port") == "False", "db_port must be False"
    assert options.get("db_user") == "odoo", "db_user must be odoo"
    assert options.get("proxy_mode") == "True", "proxy_mode must be True"
    assert options.get("workers") == "5", "workers must be 5"
    assert options.get("limit_memory_soft") == "2684354560", "limit_memory_soft must be 2.5GB"
    assert options.get("limit_memory_hard") == "5368709120", "limit_memory_hard must be 5.0GB"
    print("PASS: odoo.prod.conf validation succeeded.")

if __name__ == "__main__":
    test_odoo_prod_conf()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python tests/test_configs.py`  
Expected: FAIL with `AssertionError: Configuration file not found`

- [ ] **Step 3: Create `odoo/config/odoo.prod.conf`**

Create `odoo/config/odoo.prod.conf` with the following content:

```ini
[options]
; Database settings
db_host = False
db_port = False
db_user = odoo
db_password = 2bund2nc3+
db_name = yyy_prod
dbfilter = ^yyy_prod$
list_db = False

; Server settings
addons_path = /usr/lib/python3/dist-packages/odoo/addons,/opt/odoo12/custom/addons,/opt/odoo12/custom/cml_addons,/opt/odoo12/custom/ph_payroll,/opt/odoo12/custom/submodule/web,/opt/odoo12/custom/submodule/stock-logistics-warehouse
data_dir = /var/lib/odoo
proxy_mode = True

; Performance & Concurrency settings
workers = 5
max_cron_threads = 1
limit_time_cpu = 600
limit_time_real = 1200
limit_memory_soft = 2684354560
limit_memory_hard = 5368709120
limit_request = 8192

; Logging settings
logfile = False
log_level = info
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python tests/test_configs.py`  
Expected: PASS with `PASS: odoo.prod.conf validation succeeded.`

- [ ] **Step 5: Commit**

```bash
git add tests/test_configs.py odoo/config/odoo.prod.conf
git commit -m "feat(prod): add production odoo configuration with strict dbfilter"
```

---

### Task 2: Create Production Reverse Proxy Configuration (`proxy/vhost.d/yyy.on-cloud.io`)

**Files:**
- Create: `proxy/vhost.d/yyy.on-cloud.io`
- Modify: `tests/test_configs.py`

**Interfaces:**
- Consumes: Nginx vhost architecture for domain `yyy.on-cloud.io`
- Produces: Nginx virtual host tuning for request body size and long timeouts

- [ ] **Step 1: Add test for proxy vhost file**

Add `test_nginx_prod_vhost()` to `tests/test_configs.py`:

```python
def test_nginx_prod_vhost():
    vhost_path = os.path.join(os.path.dirname(__file__), "..", "proxy", "vhost.d", "yyy.on-cloud.io")
    assert os.path.exists(vhost_path), f"Nginx vhost file not found: {vhost_path}"
    with open(vhost_path, "r") as f:
        content = f.read()
    assert "client_max_body_size 100m;" in content
    assert "proxy_read_timeout 600s;" in content
    print("PASS: proxy/vhost.d/yyy.on-cloud.io validation succeeded.")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -c "import sys; sys.path.insert(0, '.'); from tests.test_configs import test_nginx_prod_vhost; test_nginx_prod_vhost()"`  
Expected: FAIL with `AssertionError: Nginx vhost file not found`

- [ ] **Step 3: Create `proxy/vhost.d/yyy.on-cloud.io`**

Create `proxy/vhost.d/yyy.on-cloud.io`:

```nginx
client_max_body_size 100m;
proxy_read_timeout 600s;
proxy_connect_timeout 600s;
proxy_send_timeout 600s;

# Ensure longpolling is proxied properly if needed
location /longpolling {
    proxy_pass http://yyy.on-cloud.io;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Real-IP $remote_addr;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -c "import sys; sys.path.insert(0, '.'); from tests.test_configs import test_nginx_prod_vhost; test_nginx_prod_vhost()"`  
Expected: PASS with `PASS: proxy/vhost.d/yyy.on-cloud.io validation succeeded.`

- [ ] **Step 5: Commit**

```bash
git add proxy/vhost.d/yyy.on-cloud.io tests/test_configs.py
git commit -m "feat(prod): add nginx reverse proxy vhost tuning for yyy.on-cloud.io"
```

---

### Task 3: Create Production Docker Compose File (`odoo/docker-compose.prod.yml`)

**Files:**
- Create: `odoo/docker-compose.prod.yml`
- Modify: `tests/test_configs.py`

**Interfaces:**
- Consumes: `odoo/Dockerfile`, `odoo/config/odoo.prod.conf`
- Produces: Docker Compose service `web-prod` running container `odoo-web-prod`

- [ ] **Step 1: Add test for production compose specification**

Add `test_docker_compose_prod()` to `tests/test_configs.py`:

```python
def test_docker_compose_prod():
    compose_path = os.path.join(os.path.dirname(__file__), "..", "odoo", "docker-compose.prod.yml")
    assert os.path.exists(compose_path), f"Compose file not found: {compose_path}"
    with open(compose_path, "r") as f:
        content = f.read()
    assert "container_name: odoo-web-prod" in content
    assert "127.0.0.1:8079:8069" in content
    assert "VIRTUAL_HOST=yyy.on-cloud.io" in content
    assert "LETSENCRYPT_HOST=yyy.on-cloud.io" in content
    assert "odoo_odoo-web-prod-data:/var/lib/odoo" in content
    assert "./config/odoo.prod.conf:/etc/odoo/odoo.conf" in content
    assert "/var/run/postgresql:/var/run/postgresql" in content
    print("PASS: docker-compose.prod.yml validation succeeded.")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -c "import sys; sys.path.insert(0, '.'); from tests.test_configs import test_docker_compose_prod; test_docker_compose_prod()"`  
Expected: FAIL with `AssertionError: Compose file not found`

- [ ] **Step 3: Create `odoo/docker-compose.prod.yml`**

Create `odoo/docker-compose.prod.yml`:

```yaml
services:
  web-prod:
    build: .
    image: odoo12-py37
    container_name: odoo-web-prod
    ports:
      - "127.0.0.1:8079:8069"
    environment:
      - VIRTUAL_HOST=yyy.on-cloud.io
      - VIRTUAL_PORT=8069
      - LETSENCRYPT_HOST=yyy.on-cloud.io
      - LETSENCRYPT_EMAIL=renato@cml-intl.com
      - HOST=False
      - USER=odoo
      - PASSWORD=2bund2nc3+
    volumes:
      - odoo_odoo-web-prod-data:/var/lib/odoo
      - ./config/odoo.prod.conf:/etc/odoo/odoo.conf
      - ./addons:/opt/odoo12/custom
      - /var/run/postgresql:/var/run/postgresql
    networks:
      - nginx-proxy-network
    restart: always

volumes:
  odoo_odoo-web-prod-data:
    external: true

networks:
  nginx-proxy-network:
    external: true
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -c "import sys; sys.path.insert(0, '.'); from tests.test_configs import test_docker_compose_prod; test_docker_compose_prod()"`  
Expected: PASS with `PASS: docker-compose.prod.yml validation succeeded.`

- [ ] **Step 5: Commit**

```bash
git add odoo/docker-compose.prod.yml tests/test_configs.py
git commit -m "feat(prod): add production docker-compose definition for odoo-web-prod"
```

---

### Task 4: Create Production Deployment Script (`deploy-prod.sh`)

**Files:**
- Create: `deploy-prod.sh`
- Modify: `tests/test_configs.py`

**Interfaces:**
- Consumes: `odoo/docker-compose.prod.yml`, `odoo/config/odoo.prod.conf`, `proxy/docker-compose.yml`
- Produces: Executable deployment script `deploy-prod.sh` for one-command production rollouts

- [ ] **Step 1: Add test for production deployment script**

Add `test_deploy_prod_script()` to `tests/test_configs.py`:

```python
def test_deploy_prod_script():
    script_path = os.path.join(os.path.dirname(__file__), "..", "deploy-prod.sh")
    assert os.path.exists(script_path), f"Deployment script not found: {script_path}"
    with open(script_path, "r") as f:
        content = f.read()
    assert "odoo-web-prod" in content
    assert "yyy.on-cloud.io" in content
    assert "odoo_odoo-web-prod-data" in content
    assert "8079:8069" in content
    assert "odoo.prod.conf" in content
    # Ensure staging is not killed
    assert "docker rm -f odoo-web " not in content, "Script must not stop the staging container odoo-web"
    print("PASS: deploy-prod.sh validation succeeded.")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -c "import sys; sys.path.insert(0, '.'); from tests.test_configs import test_deploy_prod_script; test_deploy_prod_script()"`  
Expected: FAIL with `AssertionError: Deployment script not found`

- [ ] **Step 3: Create `deploy-prod.sh`**

Create `deploy-prod.sh` with executable permissions:

```bash
#!/bin/bash
# Odoo 12 Production Docker Deployment Script
# Fully isolated from staging environment

set -e

# Ensure we are running from the directory where the script is located
cd "$(dirname "$0")"

echo "==> Pulling latest changes from GitHub..."
git pull
git submodule update --init --recursive

echo "==> Ensuring Docker networks and production volumes exist..."
docker network create nginx-proxy-network 2>/dev/null || true
docker volume create odoo_odoo-web-prod-data 2>/dev/null || true

# Determine compose command
COMPOSE_CMD="docker compose"
if ! docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
fi

echo "==> Ensuring Nginx reverse proxy & SSL companion are running..."
if [ -d "proxy" ]; then
    $COMPOSE_CMD -f proxy/docker-compose.yml up -d
    docker exec nginx-proxy nginx -s reload 2>/dev/null || true
fi

echo "==> Ensuring Host PostgreSQL is running..."
if command -v systemctl >/dev/null 2>&1; then
    if ! systemctl is-active --quiet postgresql; then
        echo "Starting PostgreSQL on host..."
        sudo systemctl start postgresql
    fi
fi

# Build the custom docker image if it doesn't exist
if ! docker image inspect odoo12-py37 >/dev/null 2>&1; then
    echo "==> Custom Docker image 'odoo12-py37' not found. Building it now..."
    docker build -t odoo12-py37 odoo/
fi

echo "==> Fixing addon file permissions (UID 101 = odoo user inside container)..."
sudo chown -R 101:101 $(pwd)/odoo/addons/ 2>/dev/null || echo "⚠️ Warning: Could not chown addons. You may need to run this script with sudo."

echo "==> Restarting Production Odoo container (odoo-web-prod)..."
# Remove the old production container if it exists
docker rm -f odoo-web-prod 2>/dev/null || true

# Run the new production container
docker run -d \
  --name odoo-web-prod \
  --network nginx-proxy-network \
  -p 127.0.0.1:8079:8069 \
  -e VIRTUAL_HOST=yyy.on-cloud.io \
  -e VIRTUAL_PORT=8069 \
  -e LETSENCRYPT_HOST=yyy.on-cloud.io \
  -e LETSENCRYPT_EMAIL=renato@cml-intl.com \
  -e HOST=False \
  -e USER=odoo \
  -e PASSWORD=2bund2nc3+ \
  -v odoo_odoo-web-prod-data:/var/lib/odoo \
  -v $(pwd)/odoo/config/odoo.prod.conf:/etc/odoo/odoo.conf \
  -v $(pwd)/odoo/addons:/opt/odoo12/custom \
  -v /var/run/postgresql:/var/run/postgresql \
  --restart always \
  odoo12-py37

echo "==> Waiting for Production Odoo to start..."
sleep 5

echo "==> Last 20 lines of Production Odoo log:"
docker logs --tail 20 odoo-web-prod

echo ""
echo "✅ Done! Access Production Odoo at https://yyy.on-cloud.io"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -c "import sys; sys.path.insert(0, '.'); from tests.test_configs import test_deploy_prod_script; test_deploy_prod_script()"`  
Expected: PASS with `PASS: deploy-prod.sh validation succeeded.`

- [ ] **Step 5: Run full test suite**

Run: `python -m unittest tests/test_configs.py` (or `python tests/test_configs.py`)  
Expected: All tests pass.

- [ ] **Step 6: Commit**

```bash
git add deploy-prod.sh tests/test_configs.py
git commit -m "feat(prod): add deploy-prod.sh for automated production rollout"
```

---

### Task 5: Update Documentation & Setup Guide (`SETUP_SUMMARY.md`)

**Files:**
- Modify: `SETUP_SUMMARY.md`

**Interfaces:**
- Consumes: Staging and Production architecture definitions
- Produces: Updated `SETUP_SUMMARY.md` documenting both environments, host port mappings, database isolation, and deployment instructions

- [ ] **Step 1: Update `SETUP_SUMMARY.md`**

Add a dedicated section "Staging vs Production Multi-Environment Setup" to `SETUP_SUMMARY.md` detailing:
1. Container names (`odoo-web` vs `odoo-web-prod`).
2. Domains and SSL certificates (`yyy-staging.on-cloud.io` vs `yyy.on-cloud.io`).
3. Port mappings (`127.0.0.1:8069` vs `127.0.0.1:8079`).
4. Database initialization command for host PostgreSQL (`sudo -u postgres createdb -O odoo yyy_prod`).
5. Deployment command (`./deploy-prod.sh`).

- [ ] **Step 2: Commit**

```bash
git add SETUP_SUMMARY.md
git commit -m "docs: document production environment architecture in SETUP_SUMMARY.md"
```
