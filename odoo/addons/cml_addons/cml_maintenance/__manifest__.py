# -*- coding: utf-8 -*-
{
    'name': "CML - Maintenance",

    'summary': """Custom View for Maintenance Module""",

    'description': """
        * Add Image on Equipment View
        """,

    'author': "CML",
    'website': "www.cml-intl.com",
    'category': 'Manufacturing',
    'version': '12.0.1',

    # any module necessary for this one to work correctly
    'depends': ['maintenance'],

    # always loaded
    'data': [
        'views/maintenance_equipment.xml',
          ],
}
