{
    'name': 'PH Payroll Employee Documents',
    'version': '12.0.3',
    'summary': """Manages Employee Documents With Expiry Notifications.""",
    'description': """OH Addon: Manages Employee Related Documents with Expiry Notifications.""",
    'category': 'Generic Modules/Human Resources',
    'author': 'Cybrosys Technologies Pvt. Ltd.',
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/employee_document_view.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False
}
