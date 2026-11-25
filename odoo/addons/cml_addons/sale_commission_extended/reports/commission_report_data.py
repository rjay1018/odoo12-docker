# -*- coding: utf-8 -*-
"""Shared data-grouping helpers for Customer and Invoice commission reports.

Kept free of top-level Odoo imports so both QWeb reports, HTTP Excel
controllers, and standalone unit tests can reuse the exact same math.
"""


def _resolve_invoice_line(line):
    inv_line = getattr(line, 'invoice_line', False)
    if not inv_line:
        agent_line = getattr(line, 'agent_line', False)
        agent_line_categ = getattr(line, 'agent_line_categ', False)
        if agent_line:
            inv_line = agent_line[:1].object_id
        elif agent_line_categ:
            inv_line = agent_line_categ[:1].object_id
    return inv_line


def _format_date(val):
    if not val:
        return ''
    if hasattr(val, 'strftime'):
        return val.strftime('%Y-%m-%d')
    return str(val)


def _format_commission_rate(commission, subtotal=0.0):
    if not commission:
        return ''
    ctype = getattr(commission, 'commission_type', False)
    if ctype == 'pct':
        return '%g%%' % (commission.fix_qty or 0.0)
    if ctype == 'fix':
        return 'Fixed ({:,.2f})'.format(commission.fix_qty or 0.0)
    if ctype == 'section':
        abs_sub = abs(subtotal or 0.0)
        for sec in (getattr(commission, 'sections', None) or []):
            if sec.amount_from <= abs_sub <= sec.amount_to:
                return '%g%%' % (sec.percent or 0.0)
        return getattr(commission, 'name', '') or ''
    return getattr(commission, 'name', '') or ''


def _iter_settlement_lines(settlement):
    all_lines = list(getattr(settlement, 'lines', None) or [])
    categ_lines = getattr(settlement, 'categ_lines', None)
    if categ_lines:
        all_lines.extend(list(categ_lines))
    return all_lines


def _build_normalized_entries(settlement):
    """Return deduplicated per-invoice-line entries for a settlement.

    Credit notes (invoice.type containing 'refund') automatically negate
    quantity, line total, and (as a guard) commission amount.
    """
    entries_by_key = {}
    settlement_agent = getattr(settlement, 'agent', False)
    default_agent_name = settlement_agent.name if settlement_agent else ''

    for idx, line in enumerate(_iter_settlement_lines(settlement)):
        inv_line = _resolve_invoice_line(line)
        invoice = getattr(line, 'invoice', False) or (inv_line.invoice_id if inv_line else False)
        partner = invoice.partner_id if invoice else False
        product = inv_line.product_id if inv_line else False
        commission = getattr(line, 'commission', False)

        inv_type = getattr(invoice, 'type', '') or '' if invoice else ''
        is_refund = 'refund' in inv_type
        sign = -1.0 if is_refund else 1.0

        inv_line_id = inv_line.id if inv_line else False
        invoice_id = invoice.id if invoice else False
        key = (invoice_id, inv_line_id) if inv_line_id else (invoice_id, 'line-%d' % idx)

        raw_subtotal = (inv_line.price_subtotal or 0.0) if inv_line else 0.0
        rate_str = _format_commission_rate(commission, raw_subtotal)

        if key not in entries_by_key:
            inv_name = (invoice.number or invoice.name or 'No Invoice') if invoice else 'No Invoice'
            inv_date = _format_date(
                getattr(invoice, 'date_invoice', False) if invoice else getattr(line, 'date', False)
            )
            line_agent = getattr(line, 'agent', False)
            agent_name = (line_agent.name if line_agent else '') or default_agent_name
            entries_by_key[key] = {
                'partner_id': partner.id if partner else False,
                'partner': partner.name if partner else 'No Customer',
                'invoice_id': invoice_id,
                'invoice': inv_name,
                'invoice_date': inv_date,
                'agent': agent_name,
                'product': product.name if product else 'No Product',
                'uom': inv_line.uom_id.name if inv_line and getattr(inv_line, 'uom_id', False) else '',
                'quantity': sign * ((inv_line.quantity or 0.0) if inv_line else 0.0),
                'unit_price': (inv_line.price_unit or 0.0) if inv_line else 0.0,
                'price_subtotal': sign * raw_subtotal,
                '_rates': [],
                'commission_rate': '',
                'commission_amount': 0.0,
                'is_refund': is_refund,
            }

        entry = entries_by_key[key]
        if rate_str and rate_str not in entry['_rates']:
            entry['_rates'].append(rate_str)
            entry['commission_rate'] = ' + '.join(entry['_rates'])

        comm_amt = getattr(line, 'settled_amount', 0.0) or 0.0
        if is_refund and comm_amt > 0:
            comm_amt = -comm_amt
        entry['commission_amount'] += comm_amt

    return list(entries_by_key.values())


def get_by_customer_data(settlement):
    """Group settlement entries by customer with customer subtotals and grand totals."""
    grouped = {}
    grand_total_sales = 0.0
    grand_total_commission = 0.0

    for entry in _build_normalized_entries(settlement):
        p_key = entry['partner_id']
        if p_key not in grouped:
            grouped[p_key] = {
                'partner': entry['partner'],
                'lines': [],
                'total_sales': 0.0,
                'total_commission': 0.0,
            }
        cust = grouped[p_key]
        cust['lines'].append(entry)
        cust['total_sales'] += entry['price_subtotal']
        cust['total_commission'] += entry['commission_amount']
        grand_total_sales += entry['price_subtotal']
        grand_total_commission += entry['commission_amount']

    customers = list(grouped.values())
    customers.sort(key=lambda c: (c['partner'] or '').lower())
    for cust in customers:
        cust['lines'].sort(key=lambda l: (
            l['invoice_date'] or '',
            l['invoice'] or '',
            (l['product'] or '').lower(),
        ))

    return {
        'customers': customers,
        'grand_total_sales': grand_total_sales,
        'grand_total_commission': grand_total_commission,
    }


def get_by_invoice_data(settlement):
    """Group settlement entries by invoice with invoice subtotals and grand totals."""
    grouped = {}
    grand_total_sales = 0.0
    grand_total_commission = 0.0

    for entry in _build_normalized_entries(settlement):
        inv_key = entry['invoice_id'] or entry['invoice']
        if inv_key not in grouped:
            grouped[inv_key] = {
                'invoice': entry['invoice'],
                'invoice_date': entry['invoice_date'],
                'partner': entry['partner'],
                'agent': entry['agent'],
                'lines': [],
                'total_sales': 0.0,
                'total_commission': 0.0,
            }
        inv = grouped[inv_key]
        inv['lines'].append(entry)
        inv['total_sales'] += entry['price_subtotal']
        inv['total_commission'] += entry['commission_amount']
        grand_total_sales += entry['price_subtotal']
        grand_total_commission += entry['commission_amount']

    invoices = list(grouped.values())
    invoices.sort(key=lambda i: (i['invoice_date'] or '', i['invoice'] or ''))
    for inv in invoices:
        inv['lines'].sort(key=lambda l: (l['product'] or '').lower())

    return {
        'invoices': invoices,
        'grand_total_sales': grand_total_sales,
        'grand_total_commission': grand_total_commission,
    }
