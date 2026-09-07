# -*- coding: utf-8 -*-
{
    'name': "CML - manufacturing costing",

    'summary': """manufacturing costing""",

    'description': """
        * manufacturing costing
        """,

    'author': "CML",
    'website': "www.cml-intl.com",
    'category': 'Manufacturing',
    'version': '12.0.12',

    # any module necessary for this one to work correctly
    'depends': ['bi_odoo_process_costing_manufacturing', 'mrp_byproduct', 'stock'],

    # always loaded
    'data': [
        'views/bom_operation.xml',
        'views/mrp_production_custom_view.xml',
        'views/stock_move_line_custom_view.xml',
        'views/stock_picking_custom_view.xml',
        'views/stock_product_category_view.xml',
        'views/stock_picking_type_view.xml'
    ],
}
