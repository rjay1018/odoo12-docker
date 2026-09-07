# -*- coding: utf-8 -*-
# Part of CML Transformative. See LICENSE file for full copyright and licensing details.
{
    'name': "Clinic Appoitment Extension",
    'summary': "Clinic Appoitment Extension",
    'description': """
- Extension of Appointment Management
    - Create Invoice From Appointment
    - Client can see own appointment in my account
    - Client can add feedback from my account 
""",
    "version": "1.9",
    "category": "portal",
    'author': "CML Transformative",
    'website': "www.transformative.asia",
    'license': 'Other proprietary',
    "depends": [
        'cml_clinic','cml_helpline'
    ],
    "data": [
        'security/ir.model.access.csv',
        'wizards/invoice_wizard_view.xml',
        'views/appointment_view.xml',
        'views/appointment_template.xml',
        'views/partner_view.xml',
        'views/account_invoice_view.xml',
        'views/account_payment_view.xml',
        'views/res_clinic_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
