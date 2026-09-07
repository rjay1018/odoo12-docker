# -*- coding: utf-8 -*-
# Part of Kiran Infosoft. See LICENSE file for full copyright and licensing details.
{
    'name': "Ki Account Restriction",
    'summary': "Ki Account Restriction",
    'description': "Ki Account Restriction",
    "version": "1.3",
    "category": "Website",
    'author': "Kiran Infosoft",
    "website": "http://www.kiraninfosoft.com",
    'license': 'Other proprietary',
    "depends": ['account'],
    "data": [
        'security/ir.model.access.csv',
        'security/account_restriction.xml',
        'views/account_restriction_view.xml',
    ],
    "application": False,
    'installable': True,
}




