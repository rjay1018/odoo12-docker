# -*- coding: utf-8 -*-
# Part of Kiran Infosoft. See LICENSE file for full copyright and licensing details.
{
    'name': "Sales Consignment",
    'summary': """Sales Consignment""",
    'description': """Sales Consignment""",
    "version": "3.8",
    'author': "Kiran Infosoft",
    "website": "http://www.kiraninfosoft.com",
    'license': 'Other proprietary',
    "depends": [
        'sale_stock',
    ],
    "data": [
        'security/ir.model.access.csv',
        'data/data.xml',
        'report/consignment_report.xml',
        'views/sales_consignment.xml',
        'views/sale.xml',
        'views/server_action.xml',
        'views/change_invoice_journal_wizard_view.xml',
    ],
    "application": False,
    'installable': True,
}
