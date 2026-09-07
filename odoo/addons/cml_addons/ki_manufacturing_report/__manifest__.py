{
    'name': "KI Manufacturing Report",
    'summary': "KI Manufacturing Report",
    'description': """ 
            This module Manufacturing Report.
     """,
    'author': "KI Manufacturing Report",
    'category': 'Account',
    'version': '0.1',
    'depends': ['mrp'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/manufacturing_report_wizard_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1,
}
