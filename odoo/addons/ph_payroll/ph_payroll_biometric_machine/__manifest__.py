{
    "name" : "ZK Biometric Device Integration Kware (ZKTECO)",
    "version" : "1.0",
    "author" : "JUVENTUD PRODUCTIVA VENEZOLANA, Allan J. Manuel",
    "category" : "Human Resources",
    "website" : "https://www.youtube.com/channel/UCTj66IUz5M-QV15Mtbx_7yg",
    "description": "Module for the integration between ZK Biometric Machines and Odoo.",
    'license': 'OPL-1',
    "depends" : ["base", 'hr', 'ph_payroll_attendance'],
    "data" : [
        "wizard/zk_create_users_wizard.xml",
        "views/biometric_machine_view.xml",
        "data/cron.xml",
        # "security/res_groups.xml",
        "security/ir.model.access.csv"
    ],
    'images': ['static/images/zk_screenshot.gif'],
    "active": True,
    "installable": True,
    'currency': 'EUR',
    'price': 99.00,
    'qweb': [
        "static/src/xml/machine_attendance.xml",
    ]
}
