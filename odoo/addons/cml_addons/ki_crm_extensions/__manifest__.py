# -*- coding: utf-8 -*-
{
    'name': "CRM EXTENSION",

    'summary': """CRM EXTENSION""",

    'description': """
        """,

    'author': "CML",
    'website': "www.cml-intl.com",
    'category': 'crm',
    'version': '0.4',

    'depends': ['base', 'crm', 'cml_clinic'],

    'data': [
        'security/ir.model.access.csv',
        'wizard/crm_appointment_wizard_view.xml',
        'views/crm_lead_view.xml',
    ],
}
