# -*- coding: utf-8 -*-
# Copyright 2017 Renato B. Lopez Jr. CML - Transformative Coaching and Consulting Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "CML - Partner Reference",

    'summary': """Add related partner reference for customer and vendor invoices""",

    'description': """
        """,

    'author': "CML",
    'website': "www.cml-intl.com",
    'category': 'Accounting',
    'version': '12.0.1',

    # any module necessary for this one to work correctly
    'depends': ['account'],

    # always loaded
    'data': ['data/ir_sequence_data.xml',
             'views/account_invoice_view.xml',
             'views/res_partner.xml'
          ],
    'installable': True,
    'auto_install': False,
}