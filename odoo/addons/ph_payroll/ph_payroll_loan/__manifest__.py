{
    'name': 'PH Payroll Loan Management',
    'version': '12.0.3',
    'summary': 'Manage Loan Requests',
    'description': """
        Helps you to manage Loan Requests of your company's staff.
        """,
    'category': 'Generic Modules/Human Resources',
    'author': "Cybrosys Technologies Pvt. Ltd., Allan J. Manuel",
    'depends': ['hr_payroll'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/loan_seq.xml',
        'data/salary_rule_loan.xml',
        'views/loan.xml',
        'views/canteen.xml',
        'views/configuration.xml',
    ],
    'demo': [],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False
}
