{
    'name': 'PH Payroll Overtime Request',
    'version': '12.0.3',
    'category': 'Generic Modules/Human Resources',
    'author': 'Allan Manuel',
    'depends': ['ph_payroll_computation'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/overtime.xml',
        # 'views/configuration.xml',
        'data/computation.xml'
    ],
    'qweb': [
        "static/src/xml/overtime.xml",
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
