# -*- coding: utf-8 -*-
{
    'name': "CML - Recruitment",

    'summary': """Recruitment Related Extension""",

    'description': """
        """,

    'author': "CML",
    'website': "www.cml-intl.com",
    'category': 'Employee',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr_recruitment'],

    # always loaded
    'data': [
          'security/ir.model.access.csv',
          'data/sequence.xml',
          'data/employee_request.xml',
          'views/hr_applicant.xml',
          'views/hr_job.xml',
          'views/hr_employee_request.xml',
          'views/hr_competency.xml',
          'views/hr_role_profile.xml',
          'views/hr_succession_plan.xml',
          'views/hr_task_inventory.xml',
          'wizards/refusal.xml',
          ],
}
