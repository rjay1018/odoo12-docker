{
    'name': 'Sales Commissions - Extended',
    'version': '12.0.14',
    'author': 'Allan J. Manuel, Rjay Lopez',
    'category': 'Sales Management',
    'license': 'AGPL-3',
    'depends': ['sale_commission'],
    'website': 'https://github.com/OCA/commission',
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/product.xml',
        'views/partner.xml',
        'views/sale_commission.xml',
        'views/sale_order.xml',
        'views/account_invoice.xml',
        'views/settlement.xml',
        'reports/commission_analysis.xml',
        'reports/settlement_report.xml',
        'reports/settlement_summary_report_template.xml',
        'reports/settlement_summary_partner_product_report_template.xml'
    ],
    'installable': True
}
