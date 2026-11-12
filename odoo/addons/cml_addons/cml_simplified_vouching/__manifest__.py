{
    'name': 'Simplified Vouching Report',
    'version': '12.0.1.0.0',
    'category': 'Warehouse',
    'license': 'AGPL-3',
    'depends': ['stock', 'sale_stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/params.xml',
        'data/cron.xml',
        'views/simplified_vouching.xml',
    ],
    'qweb': ['static/src/xml/buttons.xml'],
    'installable': True,
}
