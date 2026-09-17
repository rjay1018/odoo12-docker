# Odoo 12 Hybrid Architecture & Setup Summary

Here is the high-level summary of the latest Odoo 12 Hybrid Architecture, server configuration, and automated tooling for this repository.

---

### 1. Architecture Overview (Hybrid Model)
* **Application Layer (Docker):** Odoo 12 runs inside an isolated Docker container (`odoo-web`) on Ubuntu 20.04 with Python 3.8.
* **Database Layer (Bare-Metal Host):** **PostgreSQL 16** runs directly on the Ubuntu 24.04 host system for maximum NVMe/SSD disk I/O performance and memory caching.
* **Inter-Process Communication:** Odoo talks to PostgreSQL via a mounted **UNIX domain socket** (`/var/run/postgresql/.s.PGSQL.5432`), completely bypassing network TCP overhead.
* **SSL & Reverse Proxy Layer (Docker):** A global `nginx-proxy` and `acme-companion` stack handles domain routing (`yyy-staging.on-cloud.io`) and automated Let's Encrypt SSL renewal on ports 80 and 443.

---

### 2. Base Environment (The Dockerfile)
* **OS & Software:** Built on **Ubuntu 20.04**, running **Python 3.8**.
* **Odoo Version:** Odoo 12.0 (installed from official Odoo nightly `.deb` packages).
* **PDF Engine:** Uses `wkhtmltopdf` (v0.12.6-1) for native Odoo PDF generation.
* **Font Libraries:** Includes `fonts-urw-base35` and `gsfonts` to ensure ReportLab standard PostScript fonts (`Times-Roman`, `Helvetica`, `Courier`) render without `.pfb` warnings.
* **Java Integration:** Uses **Java 8 (`openjdk-8-jdk`)** specifically so the container can compile and run **Jasper Reports**.
* **Dependencies:** Custom Python libraries are pre-installed via pip (`aeroolib`, `pandas`, `numpy`, `plotly`, `openpyxl`, `num2words`).

---

### 3. Services & Volume Mounts
* **Web Service (`odoo-web`):**
  * Port: `8069` (HTTP) and `8072` (Longpolling / Gevent).
  * Network: Attached to `nginx-proxy-network` (external).
  * Volumes:
    * `odoo-web-data` ➔ `/var/lib/odoo` (Houses filestore attachments and sessions).
    * `./odoo/config` ➔ `/etc/odoo` (Houses `odoo.conf`).
    * `./odoo/addons` ➔ `/opt/odoo12/custom` (Houses custom addons and Jasper reports).
    * `/var/run/postgresql` ➔ `/var/run/postgresql` (Host Unix domain socket for direct DB access).

---

### 4. High-Performance Concurrency & Tuning (`odoo.conf`)
* **Multi-Worker Execution:** Configured with `workers = 5` (1 dedicated cron worker + 4 HTTP request workers) to allow multiple concurrent users without freezing.
* **Memory Limits:**
  * `limit_memory_soft = 2147483648` (2 GB)
  * `limit_memory_hard = 2684354560` (2.5 GB)
  * Workers exceeding limits are automatically recycled by Odoo to prevent memory leaks.
* **Reverse Proxy Mode:** `proxy_mode = True` ensures Odoo properly handles SSL headers (`X-Forwarded-Host`, `X-Forwarded-Proto`).
* **Database Connection:** `db_host = False` and `db_port = False` instruct psycopg2 to communicate over the local UNIX domain socket with user `odoo`.

---

### 5. Host Database Resilience & OOM Crash Shield
* **OOM Immunity:** PostgreSQL 16 on the host is protected by systemd overrides (`/etc/systemd/system/postgresql@16-main.service.d/oom.conf`):
  ```ini
  [Service]
  OOMScoreAdjust=-1000
  ```
  Even under heavy memory spikes from Jasper reports or background jobs, the Linux kernel will **never kill PostgreSQL**.
* **Authentication (`pg_hba.conf`):** Configured with `local all odoo md5` to allow password authentication over the local Unix domain socket while keeping `postgres` superuser `peer` access intact.

---

### 6. Container Startup (`custom_entrypoint.sh`)
* **F-String Compatibility:** Uses `f2format` to automatically back-port modern Python f-strings in custom addons into Python 3.5 compatible syntax on every boot.
* **Aeroo Patch:** Dynamically patches `aeroolib` using `sed` to fix Python 3 URL encoding bugs for aeroo reports.
* **Working Directory:** Boots from `/var/lib/odoo` so Jasper can write its `.pid` files without permission collisions.

---

### 7. Self-Healing Server Deployment (`deploy.sh`)
* **Automated Git Sync:** Pulls latest code from GitHub (`git pull`).
* **Proxy Stack Auto-Start:** Automatically detects and spins up `proxy/docker-compose.yml` (`nginx-proxy` + `acme-companion`) if not running.
* **Host Database Verification:** Verifies native `postgresql` is active via `systemctl`.
* **Container Cleanup:** Automatically retires and cleans up legacy containerized `odoo-db` instances.
* **Permission Auto-Fix:** Ensures UID `101:101` ownership on the `./odoo/addons` folder.
* **Container Rollout:** Restarts `odoo-web` with the `/var/run/postgresql` socket mount and virtual host SSL variables.

---

### 8. Interactive Database Migration (`restore.sh`)
* **Native Host Performance:** Drops, creates, and restores databases directly on the host using `createdb`, `dropdb`, and `psql` (bypassing container overhead).
* **Schema Permission Patching:** Automatically executes `GRANT ALL ON SCHEMA public TO odoo;` to guarantee full PostgreSQL 16 compatibility.
* **Filestore Synchronization:** Synchronizes filestores directly into the `odoo_odoo-web-data` volume using a lightweight busybox container.
* **One-Click Re-Deployment:** Seamlessly calls `deploy.sh` upon completion.
