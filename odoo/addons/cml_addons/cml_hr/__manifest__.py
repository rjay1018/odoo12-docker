# -*- coding: utf-8 -*-
{
    'name': "CML HRIS",

    'summary': """CML HRIS Customized View""",

    'description': """
        Long description of module's purpose
    """,

    'author': "CML",
    'website': "www.cml-intl.com",
    'category': 'Employee',
    'version': '0.2',

    # any module necessary for this one to work correctly
    'depends': ['hr','hr_contract', 'hr_employee_updation',
    'hr_experience','hr_recruitment', 'employee_orientation'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/contract.xml',
        'views/employee.xml',
        'views/employee_training.xml'        
    ],
    
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
