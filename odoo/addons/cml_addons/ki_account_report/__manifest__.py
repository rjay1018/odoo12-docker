{
    'name': "KI Account Report",
    'summary': "KI Account Report",
    'description': """ 
            This module Account Report.
     """,
    'author': "KI Account Report",
    'category': 'Account',
    'website': "http://www.kiraninfosoft.com",
    'version': '0.1',
    'depends': ['account','cml_accounting'],
    'data': [
        'wizard/payment_report_wizard_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1,
}
