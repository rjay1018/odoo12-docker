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
