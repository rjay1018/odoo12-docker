# Odoo 12 Migration to Hostinger (Ubuntu 24.04) Design

## 1. Architecture Overview
We will use a dual-stack Docker Compose architecture. This ensures that the Nginx proxy can be reused for other applications on your Hostinger VPS in the future.

### Stack A: Nginx Proxy (Global)
- **nginx-proxy**: Automatically routes traffic to the correct containers based on the `VIRTUAL_HOST` environment variable.
- **acme-companion**: Automatically issues and renews Let's Encrypt SSL certificates for HTTPS based on `LETSENCRYPT_HOST`.
- **Network**: `nginx-proxy-network` (an external Docker network).

### Stack B: Odoo 12 Application
- **odoo12**: The official `odoo:12.0` Docker image. (It isolates Odoo's Python 3.5 dependency from the Ubuntu 24.04 host).
- **postgres**: The `postgres:12` database image.
- **Volumes**:
  - `odoo-web-data`: Stores the filestore (attachments, sessions).
  - `./addons`: Local directory for custom modules.
  - `odoo-db-data`: Stores the PostgreSQL database.
- **Network**: Connects to both its internal DB network and the external `nginx-proxy-network`.

## 2. Directory Structure
```text
d:\DeveloperMode\ViveCode\odoo12-docker-ubuntu24\
├── proxy\
│   └── docker-compose.yml
└── odoo\
    ├── docker-compose.yml
    ├── config\
    │   └── odoo.conf
    └── addons\         (Custom modules go here)
```

## 3. Data Migration Flow
Since your data is on the old server, the migration will follow these steps:
1. **Extraction**: Export the PostgreSQL database from the old server (`pg_dump`) and archive the Odoo filestore and custom addons.
2. **Transfer**: Use `scp` or `rsync` to download the data from the old server to your local machine (or directly to Hostinger).
3. **Infrastructure Setup**: Deploy the Proxy and Odoo Docker Compose stacks on Hostinger.
4. **Restoration**: 
   - Place custom addons in the `odoo/addons` folder.
   - Restore the PostgreSQL database dump into the new `postgres` container.
   - Copy the old filestore into the `odoo-web-data` volume.
5. **Validation**: Test the application, update module lists, and verify SSL.

## 4. Error Handling & Backups
- **Postgres Versions**: We will ensure the Postgres version matches or is compatible with the old server to prevent `pg_restore` issues.
- **File Permissions**: Docker volumes for Odoo require specific UID/GID permissions (usually `odoo` user, 101:101). We will include a script to fix permissions after copying the filestore.
