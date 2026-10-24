# Production Deployment Alongside Staging: Design Spec

**Date:** 2026-10-25  
**Status:** Approved  
**Author:** Pair Programming (Antigravity & User)  

---

## 1. Executive Summary

This specification defines the setup and deployment architecture for running a dedicated **Production Odoo 12 instance** alongside the existing **Staging instance** on the same **Ubuntu 24.04** host.

The architecture follows the established hybrid model:
- **Application Layer:** Two isolated Odoo containers running in Docker: `odoo-web` (staging) and `odoo-web-prod` (production).
- **Reverse Proxy & SSL:** Existing Dockerized `nginx-proxy` and `acme-companion` route `yyy.on-cloud.io` (production) and `yyy-staging.on-cloud.io` (staging) with automated Let's Encrypt certificates.
- **Database Layer:** Single host PostgreSQL 16 server hosting separate databases (`yyy_staging` / existing, and `yyy_prod` for production), communicating over the mounted UNIX domain socket `/var/run/postgresql`.
- **Isolation Principle:** Complete separation of configuration, filestore volumes, database filters, and deployment scripts so that deploying or troubleshooting one environment never interferes with the other.

---

## 2. Architecture & Container Specifications

```mermaid
graph TD
    subgraph Host ["Ubuntu 24.04 Host"]
        subgraph NativeLayer ["Native Host Services"]
            PG["🐘 PostgreSQL 16 (Bare Metal)<br>• UNIX Socket: /var/run/postgresql<br>• DBs: yyy_staging & yyy_prod<br>• OOMScoreAdjust=-1000"]
        end

        subgraph DockerLayer ["Docker Containers (nginx-proxy-network)"]
            Proxy["🌐 nginx-proxy + acme-companion<br>• Ports: 80, 443<br>• Auto Let's Encrypt SSL"]
            
            subgraph StagingEnv ["Staging Environment"]
                OdooStaging["🧪 odoo-web<br>• Domain: yyy-staging.on-cloud.io<br>• Host Port: 127.0.0.1:8069<br>• Vol: odoo_odoo-web-data<br>• Config: odoo.conf"]
            end

            subgraph ProdEnv ["Production Environment"]
                OdooProd["🚀 odoo-web-prod<br>• Domain: yyy.on-cloud.io<br>• Host Port: 127.0.0.1:8079<br>• Vol: odoo_odoo-web-prod-data<br>• Config: odoo.prod.conf"]
            end
        end
    end

    UserProd(["👥 Production Users"]) -->|HTTPS:443 (yyy.on-cloud.io)| Proxy
    UserStage(["🧪 Testers / Staging"]) -->|HTTPS:443 (yyy-staging.on-cloud.io)| Proxy

    Proxy -->|internal:8069| OdooProd
    Proxy -->|internal:8069| OdooStaging

    OdooProd == "UNIX Socket (/var/run/postgresql)" ==> PG
    OdooStaging == "UNIX Socket (/var/run/postgresql)" ==> PG
```

### Component Comparison Table

| Resource | Staging (`odoo-web`) | Production (`odoo-web-prod`) | Purpose |
| :--- | :--- | :--- | :--- |
| **Container Name** | `odoo-web` | `odoo-web-prod` | Independent lifecycle management |
| **Domain Name** | `yyy-staging.on-cloud.io` | `yyy.on-cloud.io` | Clean subdomains |
| **Local Host Port** | `127.0.0.1:8069:8069` | `127.0.0.1:8079:8069` | Avoids port collision on loopback interface |
| **Filestore Volume** | `odoo_odoo-web-data` | `odoo_odoo-web-prod-data` | Physical attachment & session separation |
| **Config File** | `odoo/config/odoo.conf` | `odoo/config/odoo.prod.conf` | Environment-specific Odoo parameters |
| **Database Name** | Staging DB | `yyy_prod` | Dedicated database |
| **Database Filter** | None / relaxed | `dbfilter = ^yyy_prod$` | Locks production strictly to `yyy_prod` |
| **DB Manager UI** | Open / configurable | `list_db = False` | Hardened security in production |
| **Custom Addons** | `./odoo/addons` | `./odoo/addons` | Shared codebase & submodules |
| **Deployment Script** | `deploy.sh` | `deploy-prod.sh` | Isolated deployment automation |

---

## 3. Configuration & Database Details

### 3.1 Production Config (`odoo/config/odoo.prod.conf`)
- `db_host = False` (forces UNIX domain socket)
- `db_port = False`
- `db_user = odoo`
- `db_password = 2bund2nc3+`
- `db_name = yyy_prod`
- `dbfilter = ^yyy_prod$`
- `list_db = False`
- `proxy_mode = True`
- `workers = 5`
- `limit_memory_soft = 2684354560` (2.5 GB)
- `limit_memory_hard = 5368709120` (5.0 GB)
- `limit_time_cpu = 600`
- `limit_time_real = 1200`
- `addons_path = /usr/lib/python3/dist-packages/odoo/addons,/opt/odoo12/custom/addons,/opt/odoo12/custom/cml_addons,/opt/odoo12/custom/ph_payroll,/opt/odoo12/custom/submodule/web,/opt/odoo12/custom/submodule/stock-logistics-warehouse`

### 3.2 Production Compose (`odoo/docker-compose.prod.yml`)
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

### 3.3 Reverse Proxy Tuning (`proxy/vhost.d/yyy.on-cloud.io`)
```nginx
client_max_body_size 100m;
proxy_read_timeout 600s;
proxy_connect_timeout 600s;
proxy_send_timeout 600s;
```

---

## 4. Deployment Automation (`deploy-prod.sh`)

The script performs the following tasks idempotently:
1. Navigates to the repository root directory.
2. Synchronizes repository and submodules (`git pull && git submodule update --init --recursive`).
3. Ensures Docker networks (`nginx-proxy-network`) and named volumes (`odoo_odoo-web-prod-data`) exist.
4. Ensures the `nginx-proxy` and `acme-companion` containers are running.
5. Verifies native host `postgresql` is active via `systemctl`.
6. Builds image `odoo12-py37` if not already present.
7. Sets proper ownership (`101:101`) on `./odoo/addons`.
8. Restarts **only** `odoo-web-prod` container, ensuring staging (`odoo-web`) is left running.
9. Displays the latest 20 log lines from `odoo-web-prod` to confirm successful boot.

---

## 5. Verification & Testing Plan

1. **Staging Non-Interference:** Check that `odoo-web` container remains running with unchanged uptime while deploying `odoo-web-prod`.
2. **Domain & SSL Test:** Check HTTPS connectivity and certificate issuance at `https://yyy.on-cloud.io`.
3. **Database Isolation Test:** Verify that `https://yyy.on-cloud.io` loads directly into `yyy_prod` without presenting the database selector UI, and `/web/database/manager` is blocked.
4. **Socket Communication Test:** Verify queries succeed over `/var/run/postgresql` without authentication or connection errors.
5. **Filestore Isolation Test:** Create an attachment in staging and verify it is not visible or stored in the production filestore volume (`odoo_odoo-web-prod-data`).
