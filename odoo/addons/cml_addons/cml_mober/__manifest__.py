# -*- coding: utf-8 -*-
{
    'name': "CML - Mober Customized View",

    'summary': """Mober Customization Requirements""",

    'description': """
        """,

    'author': "CML",
    'website': "www.cml-intl.com",
    'category': 'Employee',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr','cml_hr','hr_disciplinary_tracking',
    'hr_contract', 'hr_employee_updation','hr_experience',
    'hr_recruitment'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
          'views/employee.xml'
          ],
}
