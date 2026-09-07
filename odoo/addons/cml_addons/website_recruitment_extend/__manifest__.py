# -*- coding: utf-8 -*-
# Part of Kiran Infosoft. See LICENSE file for full copyright and licensing details.
{
    'name': "Website Recruitment Extension",
    'summary': """ Website Recruitment Extension """,
    'description': """
Website Recruitment Extend
""",
    "version": "1.1",
    "category": "Human Resources",
    'author': "Kiran Infosoft",
    "website": "http://www.kiraninfosoft.com",
    'license': 'Other proprietary',
    'images': [],
    "depends": [
        'hr_experience',
        'website_hr_recruitment',
        'website_form'
    ],
    "data": [
        'views/hr_applicant_view.xml',
        'views/hr_employe_view.xml',
        'views/website_hr_recruitment_templates.xml'
    ],
    "application": False,
    'installable': True,
}
