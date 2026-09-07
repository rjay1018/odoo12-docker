# -*- coding: utf-8 -*-
# Part of Kiran Infosoft. See LICENSE file for full copyright and licensing details.
{
    'name': "Ki Report",
    'summary': "Ki Report",
    'description': "Ki Report",
    "version": "1.9",
    "category": "",
    'author': "Kiran Infosoft",
    "website": "http://www.kiraninfosoft.com",
    'license': 'Other proprietary',
    "depends": ['mrp', 'bi_odoo_process_costing_manufacturing', 'stock', 'fleet'],
    "data": [
        'views/costing_report_view.xml',
        'wizard/inventory_xlsx_report_view.xml',
        'wizard/fuel_xlsx_report_view.xml',
        'data/total_cost.xml',
    ],
    "application": False,
    'installable': True,
}
