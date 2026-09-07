{
    'name': 'PH Payroll Employee Info',
    'version': '12.0.3',
    'summary': """Adding Advanced Fields In Employee Master""",
    'description': 'This module helps you to add more information in employee records.',
    'category': 'Generic Modules/Human Resources',
    'author': 'Cybrosys Technologies Pvt. Ltd., Allan J. Manuel',
    'depends': ['hr', 'hr_expense', 'hr_timesheet', 'hr_attendance', 'hr_recruitment', 'hr_gamification'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_view.xml',
        'views/hr_notification.xml',
        'views/partner.xml',
        'views/configuration.xml',
        'data/cron.xml',
        'reports/employment_certificate.xml',
        'reports/employee_badge.xml'
    ],
    'demo': [],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False
}
