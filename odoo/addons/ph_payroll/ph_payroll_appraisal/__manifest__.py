{
    'name': "PH Payroll Employee Appraisal",
    'version': '12.0.3',
    'summary': """Roll out appraisal plans and get the best of your workforce""",
    'description': """Roll out appraisal plans and get the best of your workforce""",
    'category': 'Generic Modules/Human Resources',
    'author': 'Cybrosys Technologies Pvt. Ltd.',
    'depends': ['hr', 'survey'],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_appraisal_security.xml',
        'views/hr_appraisal_survey_views.xml',
        'views/hr_appraisal_form_view.xml',
        'data/hr_appraisal_stages.xml'
    ],
    'images': ["static/description/banner.jpg"],
    'license': "AGPL-3",
    'installable': True,
    'application': True,
    'auto_install': False
}
