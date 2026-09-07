# -*- coding: utf-8 -*-
{
    'name': "CML - MRP Workers Schedule",

    'summary': """Lets you assigned employee/workers on each work order""",

    'description': """
        """,

    'author': "CML",
    'website': "www.cml-intl.com",
    'category': 'Employee',
    'version': '12.0.1',

    # any module necessary for this one to work correctly
    'depends': ['mrp'],

    # always loaded
    'data': [
        'views/mrp_workorder.xml',
    ],
}
