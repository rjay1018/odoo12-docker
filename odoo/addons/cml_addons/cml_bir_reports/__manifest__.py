# -*- coding: utf-8 -*-
# Part of CML. See LICENSE file for full copyright and licensing details.
{
    'name': "BIR Reports",
    'summary': """BIR Reports""",
    'description': """BIR Reports""",
    'version': "0.5",
    'category': "CRM",
    'author': "CML",
    'website': "www.cml-intl.com",
    'license': 'Other proprietary',
    "depends": [
        'product', 'account',
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/cml_excel_report_view.xml',
        'views/bir_report_template_views.xml',
        'views/bir_report_wizard_views.xml',
    ],
    'application': False,
    'installable': True,
}
