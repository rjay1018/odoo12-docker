# -*- coding: utf-8 -*-
{
    'name': 'All in One Views',

    'author' : 'Softhealer Technologies',

    'website': 'https://www.softhealer.com',

    'support': 'support@softhealer.com',

    'version': '12.0.7',

    'category': 'Extra Tools',

    'summary': 'Show Incoming Order Lines, Display Outgoing Order Lines Module, Display  Delivery Order Lines, Show Shipment Line Views,Show Purchase Order Lines, Show Request For Quotation Lines, Show Quotation Lines, Display Sale Order Lines Odoo',

    'description': """

This module useful to show sale order/quotation/purchase order/request for quotation/incoming order/outgoing order/bill/invoice/credit note/debit note/refund lines products and other information related to it using the filter & group by option. You can easily add custom filters/groups of sale order/quotation/purchase order/request for quotation/incoming order/outgoing order/bill/invoice/credit note/debit note/refund order lines. Easy to work with sale order/quotation/purchase order/request for quotation/incoming order/outgoing order/bill/invoice/credit note/debit note/refund lines directly using the list view, form view, kanban view, search view, pivot view, graph view, calendar view.

 All In One Line Views Odoo
 Show Incoming Order Lines, Display Outgoing Order Lines Module, Display  Delivery Order Lines, Show Shipment Line Views, Show Incoming Order Lines, Display Outgoing Order Lines, Show Purchase Order  Lines, Show Request For Quotation  Lines, Show Quotation Lines, Display Sale Order Lines Odoo
 Show Incoming Order Lines, Display Outgoing Order Lines Module, Display  Delivery Order Lines, Show Shipment Line Views, Show Incoming Order Lines App, Display Outgoing Order Lines, Show Purchase Order  Lines, Show Request For Quotation  Lines, Show Quotation Lines, Display Sale Order Lines Odoo

""",

    'depends': ['sale_management', 'account', 'stock', 'purchase'],

    'data': [
        'views/account_invoice_line.xml',
        'views/stock_view.xml',
        'views/purchase_order_line.xml',
        'views/sale_order_line.xml',
    ],

    'images': ['static/description/background.png', ],
    "live_test_url": "https://youtu.be/LjAyw4WuXqw",
    'auto_install': False,
    'installable' : True,
    'application': True,

    "price": 40,
    "currency": "EUR"
}
