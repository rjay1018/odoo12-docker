# -*- coding: utf-8 -*-
# Copyright 2016, 2018 Mapolgroups

{
    "name": "Mapol Production Inspection",
    "summary": "MRP Inspection",
    "version": "12.1",
    "category": "Tools",
    'author' : 'Mapol Business Solution Pvt Ltd',
    'images': ['static/description/icon.png'],    
    'website' : 'http://www.mapolbs.com/',
    "description": """
        To check the quality for the produced product using customized checklist.
    """,
    "license": "LGPL-3",
    "installable": True,
    'application': True,
    'auto_install': False,
    "depends": [
        'base','stock','product','mrp'
    ],
    "data": [
        'security/ir.model.access.csv',
        'wizard/mrp_wizard_view.xml',
        'views/mrp_inspection_view.xml',
        'views/mrp_view.xml',
        'views/inspection_view.xml',
    ],
}
