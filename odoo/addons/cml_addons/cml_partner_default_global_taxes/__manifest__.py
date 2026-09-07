{
    'name': "Partner Default Global Taxes",
    'summary': """Global Taxes""",
    'description': """Global Taxes""",
    'category': "sale",
    'license': 'Other proprietary',
    "depends": [
        'base', 'contacts', 'ki_global_tax_discount'
    ],
    "data": [
        'views/res_partner_view.xml'
    ],
    'application': False,
    'installable': True,
}
