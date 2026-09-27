# -*- coding: utf-8 -*-
{
    'name': 'Sale Order Overdue Invoice Block',
    'version': '12.0.1.0.0',
    'summary': 'Blocks SO confirmation when customer has overdue invoices',
    'description': """
Sale Order Overdue Invoice Block
================================
Prevents confirming a Sales Order if the selected customer (or parent company)
has any open invoice whose due date is in the past.

A warning banner is shown on the SO form when overdue invoices are detected.
    """,
    'category': 'Sale',
    'author': 'CML',
    'depends': [
        'sale',
        'account',
    ],
    'data': [
        'views/sale_order_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
