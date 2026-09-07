# -*- coding: utf-8 -*-
{
    'name': "CML - Disciplinary Action",

    'summary': """Disciplinary Extend""",

    'description': """
        """,

    'author': "CML",
    'website': "www.cml-intl.com",
    'category': 'Employee',
    'version': '12.0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr_disciplinary_tracking'],

    # always loaded
    'data': [
          'views/disciplinary_action.xml'
          ],
}