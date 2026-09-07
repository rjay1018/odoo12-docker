# -*- coding: utf-8 -*-
# Part of Kiran Infosoft. See LICENSE file for full copyright and licensing details.
{
    'name': "product_uom_filter",
    'summary': """Select only UOMs that are selected in product.""",
    'description': """
        Select only UOMs that are selected in product.
    """,
    'version': "1.2",
    'category': "Extra Tools",
    'author': "Kiran Infosoft",
    'website': "http://www.kiraninfosoft.com",
    'license': 'Other proprietary',
    'depends': [
        'base',
        'purchase',
        'sale',
        'sale_stock'
    ],
    'data': [
        'views/product_template_only_form_view_inherit.xml',
        'views/view_order_form_inherit.xml',
        'views/purchase_order_from_inherit.xml',
    ],
}