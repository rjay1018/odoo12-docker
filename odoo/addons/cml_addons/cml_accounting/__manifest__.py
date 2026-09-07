# -*- coding: utf-8 -*-
{
    'name': "CML - Accounting",

    'summary': """CML Customized Accounting Module""",

    'description': """
        """,

    'author': "CML",
    'website': "www.cml-intl.com",
    'category': 'Employee',
    'version': '12.0.9',

    # any module necessary for this one to work correctly
    'depends': ['account', 'account_statement','purchase'],

    # always loaded
    'data': [
        'wizards/register_payments_view.xml',
        'views/account_payment.xml',
        'views/res_partner.xml',
        'views/invoice_view.xml',
    ],
}
