# -*- coding: utf-8 -*-
{
    'name': "CML - Workcenter and Maintenance",

    'summary': """Integrate Equipments and Work Center""",

    'description': """
        """,

    'author': "CML",
    'website': "www.cml-intl.com",
    'category': 'Manufacturing',
    'version': '12.0.1',

    # any module necessary for this one to work correctly
    'depends': ['maintenance', 'mrp'],

    # always loaded
    'data': [
        'views/maintenance_request_view.xml',
        'views/mrp_workorder_views.xml',
        'views/mrp_workcenter_views.xml',
          ],
}
