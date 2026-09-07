{
    'name': 'CML - Loan Management',
    'version': '12.0.0',
    'category': 'Generic Modules/Human Resources',
    'author': "Allan J. Manuel",
    'depends': ['ph_payroll_loan', 'ph_payroll_computation'],
    'data': [
        # 'security/ir.model.access.csv',
        'security/security.xml',
        'views/loan.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
