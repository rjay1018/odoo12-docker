# -*- coding: utf-8 -*-

{
    'name': "CML - Career Care Club",

    'summary': """Customized view for Career Care Club""",

    'description': """
        """,

    'author': "CML",
    'website': "www.cml-intl.com",
    'category': 'Employee',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['cml_clinic','cml_helpline','cml_client_profile'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/client_template_view.xml',
        'views/client_referral.xml',
        'views/partner.xml',
        'views/helpline.xml'
          ],
}
