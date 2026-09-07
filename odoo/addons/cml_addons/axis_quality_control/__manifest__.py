# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": 'Axis Quality Point Control',
    "author": "Axis Technolabs",
    "version": "12.0.1.2",
    "website": "https://www.axistechnolabs.com/",
    "category": "Quality Control",
    'summary': "Quality Point Control",
    "depends": [
        "sh_inventory_mrp_qc", 
        "sh_all_in_one_mbs",
        "mrp"
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/quality_data.xml',
        'views/qc_point_view.xml',
    ],
    "installable" : True,
    "auto_install" : False,
    "application" : True,
}
