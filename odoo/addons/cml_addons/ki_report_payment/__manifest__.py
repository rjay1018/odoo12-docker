# -*- coding: utf-8 -*-
# Part of Kiran Infosoft. See LICENSE file for full copyright and licensing details.
{
    'name': "Ki Report Payment",
    'summary': "Ki Report Payment",
    'description': "Ki Report Payment",
    "version": "1.0",
    "category": "",
    'author': "Kiran Infosoft",
    "website": "http://www.kiraninfosoft.com",
    'license': 'Other proprietary',
    "depends": ['account'],
    "data": [
        'security/ir.model.access.csv',
        'wizard/invoice_report_view.xml',
        'views/invoice_report_print_view.xml',
    ],
    "application": False,
    'installable': True,
}
