# -*- coding: utf-8 -*-
#################################################################################
# Author      : Kanak Infosystems LLP. (<http://kanakinfosystems.com/>)
# Copyright(c): 2012-Present Kanak Infosystems LLP.
# All Rights Reserved.
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <http://kanakinfosystems.com/license>
#################################################################################

{
    'name': "Custom Matrix Survey",
    'version': '1.0',
    'summary': 'This app allows handling of complex survey forms with options like multiple choice questions, custom matrix etc.',
    'description': """
Custom Matrix Survey.
================================
    """,
    'license': 'OPL-1',
    'author': "Kanak Infosystems LLP.",
    'website': "http://www.kanakinfosystems.com",
    'images': ['static/description/banner.jpg'],
    'category': 'Website',
    'depends': ['survey_crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/survey_views.xml',
        'views/custom_survey.xml',
    ],
    'application': True,
    'price': 49,
    'currency': 'EUR',
}
