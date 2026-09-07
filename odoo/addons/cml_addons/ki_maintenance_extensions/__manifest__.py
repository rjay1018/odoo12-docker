# -*- coding: utf-8 -*-
# Part of Kiran Infosoft. See LICENSE file for full copyright and licensing details.
{
    'name': "Maintenance Extensions",
    'summary': """Maintenance Extensions""",
    'description': """Maintenance Extensions""",
    "version": "1.1",
    "category": "maintenance",
    'author': "Kiran Infosoft",
    "website": "http://www.kiraninfosoft.com",
    'license': 'Other proprietary',
    # 'images': ['static/description/demo.gif'],
    "depends": [
        'maintenance', 'purchase','om_account_asset'
    ],
    "data": [
        'security/ir.model.access.csv',
        'wizard/request_partner.xml',
        'wizard/equipment_asset.xml',
        'views/maintenance_request.xml',
        'views/maintenance_equipment.xml',
        'views/maintenance_purchase_order.xml',
        'views/main_asset.xml'
    ],
    "application": False,
    'installable': True,
}
