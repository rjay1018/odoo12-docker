{
    'name': "KI Scrap Report",
    'summary': "KI Scrap Report",
    'description': """ 
            This module Scrap Report.
     """,
    'author': "KI Scrap Report",
    'category': 'Account',
    'version': '0.1',
    'depends': ['account','stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/wizard_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1,
}
