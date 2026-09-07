{
    'name': 'PH Payroll Leaves',
    'version': '12.0.3',
    'category': 'Generic Modules/Human Resources',
    'author': 'Cybrosys Technologies Pvt. Ltd., Allan J. Manuel',
    'depends': ['hr_holidays', 'ph_payroll_computation'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/fiscal_year.xml',
        'views/leave.xml',
        'views/configuration.xml',
        'data/leave_type.xml',
        'data/cron.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
