{
    'name': 'PH Payroll Attendance',
    'version': '12.0.3',
    'category': 'Generic Modules/Human Resources',
    'author': 'Cybrosys Technologies Pvt. Ltd., Allan J. Manuel',
    'depends': ['hr_attendance', 'resource', 'ph_payroll_computation', 'ph_payroll_overtime', 'report_aeroo'],
    'data': [
        'security/ir.model.access.csv',
        'views/resource.xml',
        'views/attendance.xml',
        'views/slip.xml',
        'views/nd_pay_rate.xml',
        'aeroo/attendance.xml',
        'data/nd_pay_rate.xml',
    ],
    'demo': [],
    'qweb': [
        "static/src/xml/attendance.xml",
    ],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False
}
