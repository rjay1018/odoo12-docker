# -*- coding: utf-8 -*-
{
    'name': "Binhex Dashboard Layout",

    'summary': """
        Custom Odoo portal.""",

    'description': """
        Custom Odoo portal.A more graphical and intuitive theme for the Odoo portal.
    """,

    'website': "https://binhex.es/",
    'currency': 'EUR',
    'version': '1.0.1',
    'author': "Binhex Systems Solutions",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','portal'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/my_account.xml',
        'views/perfil.xml',
        'views/portal_layout.xml',
        'views/portal_view.xml',
    ],
}
