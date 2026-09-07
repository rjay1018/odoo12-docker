# -*- coding: utf-8 -*-
{
    'name': "CML - Customized for YYY and ERSAO",

    'summary': """Customized views for YYY and ERSAO as requested""",

    'description': """
        """,

    'author': "CML",
    'website': "www.cml-intl.com",
    'category': 'Custom',
    'version': '12.0.4.9',

    # any module necessary for this one to work correctly
    'depends': [
        'mail',
        'sale',
        'hr_contract',
        'product',
        'stock',
        'fleet',
        'purchase',
        'ph_payroll_overtime',
        'bi_rma'
        ],

    # always loaded
    'data': [
        'security/security.xml',
        'views/fleet.xml',
        'views/hr.xml',
        'views/product.xml',
        'views/purchase.xml',
        'views/scrap.xml',
        'views/hr_expense.xml',
        'views/overtime.xml',
        'views/rma.xml',
        'views/mrp_production_view.xml',
        'views/hr_announcement_inherit_view.xml',
        'views/account_invoice_inherit.xml',
        'views/res_partner.xml'
    ],
}
