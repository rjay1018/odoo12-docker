# Odoo 12 Docker Architecture & Setup Summary

Here is a high-level summary of the current Odoo 12 Docker architecture and setup for this repository.

### 1. Base Environment (The Dockerfile)
* **OS & Software:** Built on **Ubuntu 20.04**, running **Python 3.8**.
* **Odoo Version:** Odoo 12.0 (installed from the official Odoo nightly `.deb` packages).
* **PDF Engine:** Uses `wkhtmltopdf` (v0.12.6-1) for native Odoo PDF generation.
* **Java Integration:** We use **Java 8 (`openjdk-8-jdk`)** specifically so the container can compile and run **Jasper Reports**.
* **Dependencies:** Custom Python libraries are pre-installed via pip (e.g., `aeroolib`, `pandas`, `plotly`, `openpyxl`) to support various custom addons.

### 2. Architecture & Services (docker-compose)
* **Web Service (Odoo):** The main Odoo container runs the custom image and exposes port `8069`. It is connected to an external `nginx-proxy-network`, which means an NGINX reverse proxy handles the domains and SSL certificates.
* **Database Service:** A dedicated **PostgreSQL 12** container running on an isolated internal network (`internal-db`).
* **Volume Mounts:**
  * `./config` ➔ `/etc/odoo` (Houses the `odoo.conf` file).
  * `./addons` ➔ `/mnt/extra-addons` (Houses all custom modules, Jasper reports, and synced submodules).
  * Named volumes are used to safely persist Odoo filestore data and Postgres database data across reboots.

### 3. Container Startup (custom_entrypoint.sh)
* Before Odoo actually boots, a custom bash script runs every time the container starts.
* It uses `f2format` to scan the `addons` directory and automatically back-ports modern Python f-strings into older Python formats (acting as a Python 3.5 compatibility layer).
* It ensures Odoo boots up using `/var/lib/odoo` as its working directory (which prevents permission errors when Jasper tries to write its `.pid` file).

### 4. Live Server Deployment (deploy.sh)
* When code is pushed to GitHub, `deploy.sh` is used on the live Linux server to go live.
* The script automates pulling the code, fixing Linux file permissions (setting UID `101` for the internal `odoo` user), removing the old container, and spinning up the fresh container with all the correct environment variables and volume mounts. 

### 5. Jasper Reports Workflow
* Jasper requires `.java` files to be compiled into `.class` files. 
* Because the `addons` folder is a mounted volume, compiling the files manually once using `docker exec` saves the compiled `.class` files permanently to the host.
* Odoo will seamlessly fire up the Jasper server on-demand to print reports!
