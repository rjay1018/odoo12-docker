{
    'name': 'Journal Access Filter',
    'version': '12.0.2.0.0',
    'summary': 'Restrict Accounting Overview journals by individual user assignment',
    'description': """
        Adds a 'Restricted Journal Access' security group. When a user belongs
        to this group, their Accounting Overview kanban will only display the
        exact journals assigned to them on their User Profile.
    """,
    'category': 'Accounting',
    'author': 'jaynatz',
    'website': '',
    'depends': ['account'],
    'data': [
        'security/security_groups.xml',
        'security/record_rules.xml',
        'security/ir.model.access.csv',
        'views/res_users_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
