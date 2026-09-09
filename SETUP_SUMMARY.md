# Odoo 12 Docker Architecture & Setup Summary

Here is a high-level summary of the current Odoo 12 Docker architecture, setup, and automated tooling for this repository.

### 1. Base Environment (The Dockerfile)
* **OS & Software:** Built on **Ubuntu 20.04**, running **Python 3.8**.
* **Odoo Version:** Odoo 12.0 (installed from the official Odoo nightly `.deb` packages).
* **PDF Engine:** Uses `wkhtmltopdf` (v0.12.6-1) for native Odoo PDF generation.
* **Java Integration:** We use **Java 8 (`openjdk-8-jdk`)** specifically so the container can compile and run **Jasper Reports**.
* **Dependencies:** Custom Python libraries are pre-installed via pip (e.g., `aeroolib`, `pandas`, `plotly`, `openpyxl`) to support various custom addons.

### 2. Architecture & Services
* **Web Service (Odoo):** The main Odoo container runs the custom image and exposes port `8069`. It is connected to an external `nginx-proxy-network`, which means an NGINX reverse proxy handles the domains and SSL certificates.
* **Database Service:** A dedicated **PostgreSQL 12** container running on an isolated internal network (`internal-db`).
* **Volume Mounts:**
  * `./config` ➔ `/etc/odoo` (Houses the `odoo.conf` file).
  * `./addons` ➔ `/opt/odoo12/custom` (Houses all custom modules, Jasper reports, and synced submodules. This specific mount point fixes hardcoded Jasper image paths by perfectly aligning the internal container paths with the repository structure).
  * Named volumes are used to safely persist Odoo filestore data and Postgres database data across reboots.

### 3. Container Startup (custom_entrypoint.sh)
* Before Odoo actually boots, a custom bash script runs every time the container starts.
* **F-String Compatibility:** It uses `f2format` to scan the `/opt/odoo12/custom` directory and automatically back-ports modern Python f-strings into older Python formats (acting as a Python 3.5 compatibility layer).
* **Aeroo Patch:** It dynamically patches `aeroolib` using `sed` to fix Python 3 URL encoding bugs that break aeroo payroll reports.
* It ensures Odoo boots up using `/var/lib/odoo` as its working directory (which prevents permission errors when Jasper tries to write its `.pid` file).

### 4. Self-Healing Server Deployment (deploy.sh)
* Designed for flawless, fully-automated migrations.
* **Dynamic Paths:** Can be run from any folder location on the server.
* **Self-Healing Images:** Automatically detects if the custom `odoo12-py37` Docker image is missing on the server and builds it dynamically via `docker-compose`.
* **Automated Rollout:** Pulls the latest GitHub code, fixes Linux file permissions (setting UID `101` for the internal `odoo` user), removes the old container, and spins up the fresh container. 

### 5. Interactive Database Migration (restore.sh)
* A fully interactive bash script that makes migrating databases between servers foolproof.
* Safely drops database connections by turning off the web container.
* Prompts the user for the SQL dump file and dynamically restores it into the Postgres container.
* Automatically synchronizes and fixes permissions on the Odoo filestore by mounting a temporary busybox container directly into the Docker volume, bypassing Linux host permission issues.

### 6. Jasper Reports Workflow
* Jasper requires `.java` files to be compiled into `.class` files. 
* Because the `addons` folder is a mounted volume, compiling the files manually once using `docker exec` saves the compiled `.class` files permanently to the host.
* Odoo will seamlessly fire up the Jasper server on-demand to print reports!
