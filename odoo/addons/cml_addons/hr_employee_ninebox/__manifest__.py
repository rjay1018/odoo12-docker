
# -*- coding: utf-8 -*-
###############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) All rights reserved:
#        (c) 2015  TM_FULLNAME
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses
#
###############################################################################
{
    'name': 'HR Employee NineBox',
    'summary': 'NineBox Showing on Employees based on their Potential and Performacne Ratio',
    'version': '1.0',
    'description': """NineBox Showing on Employees based on their Potential and Performacne Ratio""",
    'author': 'Ananthu Krishna',
    'maintainer': 'Ananthu Krishna',
    'website': 'http://codersfort.com',
    "images": ["images/ninebox.png"],
    'license': 'AGPL-3',
    'category': 'hr',
    'depends': ['base','hr','web'],
    'data': [
        'views/hr_employee_view.xml',
        'views/assets.xml'
    ],
    'qweb': ['static/src/xml/ninebox.xml'],
    'installable': True,
    'application': True,
    
}
