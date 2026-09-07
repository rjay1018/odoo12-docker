# -*- coding: utf-8 -*-
# Part of Kiran Infosoft. See LICENSE file for full copyright and licensing details.

{
    'name': "Survey Extensions",
    'summary': """ Survey Extensions """,
    'description': """
* Added below features on survey:
    - Added tags on question and answer
    - Added User confirmation on survey
    """,
    'author': "Kiran Infosoft",
    "website": "http://www.kiraninfosoft.com",
    'category': 'Survey',
    'version': '2.2',
    'depends': ['survey', 'cml_assesment_extend','cml_clinic_assessment'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/action.xml',
        'views/survey_answer_tag.xml',
        'views/survey_view_inherit.xml',
        'views/survey_init_inherit.xml',
        'views/survey_user_input_line_view_inherit.xml',
        'views/survey_category_view.xml',
        'views/partner_view.xml',
        'views/assesment_view.xml',
        'wizards/survey_email_compose_message.xml'
    ],
}
