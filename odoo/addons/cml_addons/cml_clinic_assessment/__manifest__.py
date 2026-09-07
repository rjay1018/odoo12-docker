# -*- coding: utf-8 -*-
{
    'name': "CML Clinic Assessment",
    'summary': """CML Clinic Assessment""",
    'description': """
    """,
    'author': "CML",
    'maintainer':'Rjay Lopez - renato@cml-intl.com',
    'website': "www.cml-intl.com",
    'category': 'CRM',
    'version': '12.0.1',
    'depends': ['cml_clinic','partner_survey'],
    'data': [
        'views/res_company.xml',
        'views/res_partner.xml',
        'views/survey_input.xml'
    ],
    'demo': [],
    'images':[],
    'installable': True,
    'application': True,
    'auto_install': False,
}