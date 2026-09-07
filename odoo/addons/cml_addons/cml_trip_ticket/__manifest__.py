# -*- coding: utf-8 -*-
{
    'name': "CML - Trip Ticket",

    'summary': """Add Fleet information on batch picking""",

    'description': """
        """,

    'author': "CML",
    'website': "www.cml-intl.com",
    'category': 'Employee',
    'version': '12.0.1',

    # any module necessary for this one to work correctly
    'depends': ['stock_picking_batch','fleet','stock_picking_batch_extended'],

    # always loaded
    'data': [
    		'views/stock_picking_batch.xml',
    		'views/fleet_vehicle_odometer.xml'
          ],
}
