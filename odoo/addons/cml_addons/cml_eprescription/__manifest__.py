# -*- coding: utf-8 -*-
{
    'name': "CML Clinic E-Prescription",
    'summary': """CML Clinic E-Prescription""",
    'description': """
    """,
    'author': "CML",
    'maintainer':'Rjay Lopez - renato@cml-intl.com',
    'website': "www.cml-intl.com",
    'category': 'Human Resources',
    'version': '12.0.1',
    'depends': ['cml_clinic','base_fontawesome', 'mail', 'web_widget_digitized_signature'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_sequence_data.xml',
        'data/mail_template.xml',
        'views/appointment.xml',
        'views/clinic_eprescription.xml'
    ],
    'demo': [],
    'images':[],
    'installable': True,
    'application': True,
    'auto_install': False,
}