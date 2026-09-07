{
    'name': 'CML - Payroll Extended',
    'version': '12.0.0',
    'category': 'Generic Modules/Human Resources',
    'author': "Allan J. Manuel",
    'depends': ['ph_payroll_computation', 'ph_payroll_attendance'],
    'data': [
        'security/ir.model.access.csv',
        # 'security/security.xml',
        'views/payroll.xml',
        'views/undertime.xml',
        'data/data.xml',
        'aeroo/reports.xml',
        'reports/payslip.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
