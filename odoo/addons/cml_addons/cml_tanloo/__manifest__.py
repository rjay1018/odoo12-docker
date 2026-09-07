# -*- coding: utf-8 -*-
{
    'name': "CML - Tanloo Customized View",

    'summary': """Tanloo Customization Requirements""",

    'description': """
        """,

    'author': "CML",
    'website': "www.cml-intl.com",
    'category': 'Warehouse',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product',],

    # always loaded
    'data': [
         'security/ir.model.access.csv',
         'views/product.xml'
          ],
}
