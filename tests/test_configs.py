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

def test_nginx_prod_vhost():
    vhost_path = os.path.join(os.path.dirname(__file__), "..", "proxy", "vhost.d", "yyy.on-cloud.io")
    assert os.path.exists(vhost_path), f"Nginx vhost file not found: {vhost_path}"
    with open(vhost_path, "r") as f:
        content = f.read()
    assert "client_max_body_size 100m;" in content
    assert "proxy_read_timeout 600s;" in content
    print("PASS: proxy/vhost.d/yyy.on-cloud.io validation succeeded.")

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
    # Ensure staging container is not killed
    assert "docker rm -f odoo-web " not in content, "Script must not stop the staging container odoo-web"
    print("PASS: deploy-prod.sh validation succeeded.")

if __name__ == "__main__":
    test_odoo_prod_conf()
    test_nginx_prod_vhost()
    test_docker_compose_prod()
    test_deploy_prod_script()
