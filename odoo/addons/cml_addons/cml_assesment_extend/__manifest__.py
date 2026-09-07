# -*- coding: utf-8 -*-
{
    'name': "CML Assesment Extension",
    'summary': """CML Assesment Extension""",
    'description': """
- Added below features related to assesments:
    - Show assesment group by page on Assesment page
    - Added total and average score
    - Show assesments in my account
    """,
    'author': "CML Transformative",
    'website': "www.transformative.asia",
    'category': 'Human Resources',
    'version': '1.2',
    'depends': [
        'survey','partner_survey'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/assesment_view.xml',
        'views/assesment_template.xml'
    ],
    'demo': [],
    'images':[],
    'installable': True,
    'application': True,
    'auto_install': False,
}