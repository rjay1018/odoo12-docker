# -*- coding: utf-8 -*-

{
    'name': "CML - Default Analytic tags on sale and purchase from product",

    'summary': """Default Analytic tags on sale and purchase from product""",

    'description': """
    Default Analytic tags on sale and purchase from product
        """,

    'author': "CML",
    'website': "www.cml-intl.com",
    'category': 'Accounting',
    'version': '12.0.1',
    'depends': ['sale', 'purchase'],
    'data': [
        'views/product_view.xml'
    ],
    'installable': True,
    'auto_install': False,
}