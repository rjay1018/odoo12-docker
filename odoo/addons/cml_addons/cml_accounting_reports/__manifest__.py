# -*- coding: utf-8 -*
{
    'name': 'CML Accounting Report',
    'version': '1.2',
    'author': 'Rjay Lopez - rjay@transformative.asia',
    'category': 'Accounting/Reporting',
    'summary': 'Customization of Accounting Reports',
    'description': """- Add aging filter for zero rows.
    """,
    'depends': ['account_dynamic_reports',],
    'data': [
        'views/views.xml',
        'wizards/partner_ageing_view.xml',
    ],
    'installable': True,
    'qweb': ['static/src/xml/view.xml',],
    'application': True,
    'license': 'LGPL-3',
    'auto_install': False,
}
