{
    'name': 'PH Payroll Custody',
    'version': '12.0.3',
    'summary': """Manage the company properties when it is in the custody of an employee""",
    'description': 'Manage the company properties when it is in the custody of an employee',
    'category': 'Generic Modules/Human Resources',
    'author': 'Cybrosys Technologies Pvt. Ltd.',
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'security/custody_security.xml',
        'views/wizard_reason_view.xml',
        'views/custody_view.xml',
        'views/hr_custody_notification.xml',
        'views/hr_employee_view.xml',
        'views/notification_mail.xml',
        'reports/custody_report.xml'
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False
}
