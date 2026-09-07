# -*- coding: utf-8 -*-
# Part of Kiran Infosoft. See LICENSE file for full copyright and licensing details.
{
    'name': "ki Appointment Management",
    'summary': "ki Appointment Management",
    'description': "ki Appointment Management",
    "version": "1.7",
    "category": "Website",
    'author': "Kiran Infosoft",
    "website": "http://www.kiraninfosoft.com",
    'license': 'Other proprietary',
    #'images': ['static/description/image.png'],
    "depends": [
        'website',
        'cml_clinic',
        'hr'
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/appointment_template.xml',
        'views/hr_employee_inherit.xml',
        'views/specialist_tags.xml'
    ],
    "application": False,
    'installable': True,
}
