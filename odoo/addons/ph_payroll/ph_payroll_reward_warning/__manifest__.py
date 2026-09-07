{
    'name': 'PH Payroll Official Announcements',
    'version': '12.0.3',
    'summary': """Managing Official Announcements""",
    'description': 'This module helps you to manage hr official announcements',
    'category': 'Generic Modules/Human Resources',
    'author': 'Cybrosys Technologies Pvt. Ltd.',
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'security/reward_security.xml',
        'views/hr_announcement_view.xml',
    ],
    'demo': [],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False
}
