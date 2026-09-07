# -*- coding: utf-8 -*-
# Part of Kiran Infosoft. See LICENSE file for full copyright and licensing details.
{
    'name': "Membership Extension",
    'summary': "Membership Extension",
    'description': "Membership Extension",
    "version": "1.2",
    "category": "Membership",
    'author': "Kiran Infosoft",
    "website": "http://www.kiraninfosoft.com",
    'license': 'Other proprietary',
    "depends": [
        'membership',
        'cml_appointment_extends',
    ],
    "data": [
        'security/ir.model.access.csv',
        'wizard/apply_free_session_wizard_view.xml',
        'views/appointment_view.xml',
        'views/product_template_view.xml',
        'views/membership_view.xml',
        'views/res_partner.xml'
    ],
    "application": False,
    'installable': True,
}
