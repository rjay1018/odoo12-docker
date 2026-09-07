# -*- coding: utf-8 -*-
{
    'name': "Employee Self Services",
    'summary': """ Employee Self Services """,
    'description': """
* Employee can see self records as belows
- Contract
- Employee
- Attendance
- Timesheet
- Payslip
- Profile Update Request
- Manpower Request
    """,
    'author': "Kiran Infosoft",
    "website": "http://www.kiraninfosoft.com",
    'license': 'Other proprietary',
    'version': '1.4',
    'depends': [
        'base',
        'hr',
        'mail',
        'hr_employee_updation',
        'hr_contract',
        'hr_payroll',
        'hr_timesheet',
        'hr_recruitment',
        'hr_attendance'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/employee_view.xml',
        'views/employee_profile_update.xml',
        'views/manpower_request_view.xml',
        'views/hr_view.xml',
        'views/menu.xml'
    ],
}
