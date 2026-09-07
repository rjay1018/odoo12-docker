{
    'name': 'PH Payroll Employee Contract',
    'version': '12.0.3',
    'category': 'Generic Modules/Human Resources',
    'author': 'Cybrosys Technologies Pvt. Ltd., Allan J. Manuel',
    'depends': ['resource', 'hr_contract', 'hr_payroll', 'hr_payroll_account'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/contract.xml',
        'views/wage_rates.xml',
        'reports/employment_certificate.xml',
        'data/regions.xml',
        'data/wage_rates.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
