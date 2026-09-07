# -*- coding: utf-8 -*-
##############################################################################
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 WebLine Apps 
##############################################################################

{
    'name': 'User Restrict to Access Product',
    'version': '12.0.1.0',
    'category': 'sale',
    'description': """
        User Restrict to Access Product 
    """,
    'summary': """
        User Restrict to Access Product \n
        user Restrict to access product by category \n
        User Restriction to access on product,sale purchase,invoice,etc
        
    """,
    'author': 'Weblineapps',
    'website': 'webline apps@gmail.com ',
    'depends': ['sale','base'],
    'data': [
        'security/security.xml',
        'views/user_view.xml',
    ],
    'price': 15.00,
    'images' : ['static/description/banner.png'],
	'currency': 'USD',
    'installable': True,
    'auto_install': False,
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
