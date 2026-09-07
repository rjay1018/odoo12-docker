# Copyright 2020 Renato Lopez Jr. <rjay1018@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': "CML - Helpline",
    'author': "CML",
    'website': "www.cml-intl.com",
    'category': 'Employee',
    'version': '12.0.1',
    'depends': [
        'base',
        'mail',
        'cml_hr',
        'cml_clinic'
    ],
    'data': [
        'data/ir_sequence_data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/helpline.xml',
        'views/partner.xml',
        'views/employee.xml',
        'views/configurations.xml',
        'views/menu.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}