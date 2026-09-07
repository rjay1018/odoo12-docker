# -*- coding: utf-8 -*-
{
    'name': "HR Work Day Type",

    'summary': """
Manage user defined workday types and their period""",

    'description': """
This module allows users to define multiple workday types and their period for other applications to categorize work days by types. For example, overtime in normal working days, overtime in holidays, etc
    """,

    'author': 'T.V.T Marine Automation (aka TVTMA)',
    'website': 'https://www.tvtmarine.com',
    'live_test_url': 'https://v10demo-int.erponline.vn',
    'support': 'support@ma.tvtmarine.com',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Hidden',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/work_day_type_data.xml',
        'views/work_day_type_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
    'price': 0.0,
    'currency': 'EUR',
    'license': 'OPL-1',
}
