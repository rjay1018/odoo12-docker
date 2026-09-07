# -*- coding: utf-8 -*-
{
    'name': "CML - Website Registration",

    'summary': """CML - Website Registration""",

    'description': """
        """,

    'author': "CML",
    'website': "www.cml-intl.com",
    'category': 'Employee',
    'version': '12.0.1',

    # any module necessary for this one to work correctly
    'depends': ['auth_signup', 'website'],

    # always loaded
    'data': [
        'security/security.xml',
        'views/account_details_template.xml',
        'views/res_users.xml'
    ],
}
