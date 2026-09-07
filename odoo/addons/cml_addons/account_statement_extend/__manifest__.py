# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Customer/supplier statement of account reports in Odoo Extended',
    'category': 'Accounting',
    'version': '12.0.1.5',
    'summary': 'Account Statement Extra Features',

    'author': 'Kiran Infosoft',
    'website': 'https://www.kiraninfosoft.com',
    'images': [],
    'depends': ['base', 'account', 'sale_management', 'mail', 'sales_team', 'account_statement'],
    
    'data': [
             'views/res_partner_view.xml',

    ],
    'installable': True,
    'price': 36,
    'currency': "EUR",
    'auto_install': False,
    'application': True,
    "images":[],

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
