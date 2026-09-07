# -*- coding: utf-8 -*-
{
    'name': "CML - KSO Customized View",

    'summary': """KSO Customization Requirements""",

    'description': """
        """,

    'author': "CML",
    'website': "www.cml-intl.com",
    'category': 'Employee',
    'version': '0.1.1',

    # any module necessary for this one to work correctly
    'depends': ['hr','cml_hr','hr_disciplinary_tracking',
    'hr_contract', 'hr_employee_updation','hr_experience',
    'hr_recruitment'],

    # always loaded
    'data': [
          'security/ir.model.access.csv',
          'views/menu.xml',
          'views/employee.xml',
          'views/hr_experience.xml',
          'views/disciplinary_action.xml',
          'views/applicant.xml',
          'wizards/refusal.xml',
          'reports/contract_report.xml',
          'reports/reports.xml'
          ],
}
