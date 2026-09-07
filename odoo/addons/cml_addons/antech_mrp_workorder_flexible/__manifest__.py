# -*- coding: utf-8 -*-
{
    "name": """Manufacturing Order Flexible Material Consumption (from Odoo 13)""",
    "summary": """Manufacturing Order flexible material consumption in workorder just like in Odoo 13.""",
    "category": "Manufacturing",
    "version": "12.0.1.3.0",
    "auto_install": False,
    "installable": True,
    "application": False,
    "author": "ANTech Software",
    "license": "OPL-1",
    "images": [
        'images/main_screenshot.png'
    ],

    "price": 43.20,
    "currency": "EUR",
    "live_test_url": "https://demo.adiodoo.com/login_employee?login=demo&password=demo&action=mrp.mrp_production_action",
    "depends": [
        'base',
        'mrp',
        # 'stock_account'
    ],
    "data": [
        'views/mrp_bom.xml',
        'views/mrp_workorder.xml',
        'views/mrp_production.xml',
        'security/ir.model.access.csv',
    ],
    "demo": [
        # 'demo/demo.xml',
    ],
    "qweb": [
        # "static/src/xml/{QWEBFILE1}.xml",
    ],
}
