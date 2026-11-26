# -*- coding: utf-8 -*-
"""Pure-Python calculation engine for Miss Tan's Sales Performance Report.

Kept free of top-level Odoo imports so QWeb PDF, xlwt Excel, and standalone
unit tests share the exact same formulas and edge-case rules.
"""
import calendar
import datetime

MONTH_NAMES = [
    '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]

QUARTER_ORDINAL = {
    1: '1ST',
    2: '2ND',
    3: '3RD',
    4: '4TH',
}


def get_period_bounds(period_type, year, quarter=None, month=None):
    """Return (date_from, date_to, period_label, month_columns).

    month_columns is a list of (month_int, short_label) tuples:
    3 items for quarterly, 1 item for monthly.
    """
    year = int(year)
    if period_type == 'month':
        m = int(month)
        if m < 1 or m > 12:
            raise ValueError('Month must be between 1 and 12')
        last_day = calendar.monthrange(year, m)[1]
        date_from = datetime.date(year, m, 1)
        date_to = datetime.date(year, m, last_day)
        label = '%s %d' % (MONTH_NAMES[m].upper(), year)
        return date_from, date_to, label, [(m, MONTH_NAMES[m])]

    q = int(quarter)
    if q < 1 or q > 4:
        raise ValueError('Quarter must be between 1 and 4')
    start_m = (q - 1) * 3 + 1
    end_m = start_m + 2
    last_day = calendar.monthrange(year, end_m)[1]
    date_from = datetime.date(year, start_m, 1)
    date_to = datetime.date(year, end_m, last_day)
    label = '%s %d' % (QUARTER_ORDINAL[q], year)
    month_columns = [(m, MONTH_NAMES[m]) for m in range(start_m, end_m + 1)]
    return date_from, date_to, label, month_columns


def compute_sales_performance(
    agent_name,
    period_label,
    month_columns,
    invoice_lines,
    catalog_products=None,
    wholesale_prices=None,
    quota_map=None,
):
    """Aggregate invoice lines & catalog items into summary + per-product rows."""
    wholesale_prices = wholesale_prices or {}
    quota_map = quota_map or {}
    month_nums = [m for m, _ in month_columns]
    products = {}

    def _ensure_product(pid, name, category, uom):
        if pid not in products:
            products[pid] = {
                'product_id': pid,
                'item': name or 'No Product',
                'category': category or 'Uncategorized',
                'uom': uom or '',
                'total_qty': 0.0,
                'month_qtys': {m: 0.0 for m in month_nums},
                'subtotal_amount': 0.0,
                '_rates': [],
                'comm_rate': '',
                'commission_amount': 0.0,
            }
        return products[pid]

    # Seed 0-sale catalog products (e.g. from Wholesale Price List & Agent Quotas)
    for cp in (catalog_products or []):
        _ensure_product(
            cp['product_id'],
            cp.get('product_name'),
            cp.get('category_name'),
            cp.get('uom_name'),
        )

    commission_paid = 0.0
    commission_unpaid = 0.0

    for line in (invoice_lines or []):
        pid = line['product_id']
        rec = _ensure_product(
            pid,
            line.get('product_name'),
            line.get('category_name'),
            line.get('uom_name'),
        )

        inv_type = line.get('invoice_type') or 'out_invoice'
        is_refund = 'refund' in inv_type
        sign = -1.0 if is_refund else 1.0

        qty = sign * (line.get('quantity') or 0.0)
        subtotal = sign * (line.get('price_subtotal') or 0.0)
        comm_amt = line.get('commission_amount') or 0.0
        if is_refund and comm_amt > 0:
            comm_amt = -comm_amt

        rec['total_qty'] += qty
        rec['subtotal_amount'] += subtotal
        rec['commission_amount'] += comm_amt

        inv_date = line.get('invoice_date')
        if inv_date is not None:
            m = inv_date.month if hasattr(inv_date, 'month') else int(str(inv_date)[5:7])
            if m in rec['month_qtys']:
                rec['month_qtys'][m] += qty

        rate_str = line.get('commission_rate_str') or ''
        if rate_str and rate_str not in rec['_rates']:
            rec['_rates'].append(rate_str)
            rec['comm_rate'] = ' + '.join(rec['_rates'])

        if (line.get('invoice_state') or '') == 'paid':
            commission_paid += comm_amt
        else:
            commission_unpaid += comm_amt

    # Finalize per-product evaluations and summary metrics
    total_amount = 0.0
    commission_total = 0.0
    category_totals_map = {}

    above_bm_count = 0
    below_bm_count = 0
    no_sale_count = 0
    missing_wp_count = 0

    quota_pass_count = 0
    quota_fail_count = 0
    quota_na_count = 0

    rows = []
    for pid, rec in products.items():
        total_qty = rec['total_qty']
        subtotal = rec['subtotal_amount']
        comm_amt = rec['commission_amount']

        total_amount += subtotal
        commission_total += comm_amt
        cat = rec['category']
        category_totals_map[cat] = category_totals_map.get(cat, 0.0) + subtotal

        asp = (subtotal / total_qty) if total_qty > 0 else 0.0
        wp = float(wholesale_prices.get(pid, 0.0) or 0.0)
        missing_wp = (pid not in wholesale_prices) or (wp <= 0.0)

        if total_qty <= 0:
            evaluation = 'No Sale'
            no_sale_count += 1
        elif missing_wp:
            evaluation = 'No Wholesale Price'
            missing_wp_count += 1
        elif asp < wp:
            evaluation = 'Below BM'
            below_bm_count += 1
        else:
            evaluation = 'Above BM'
            above_bm_count += 1

        raw_quota = quota_map.get(pid)
        if raw_quota is not None and raw_quota > 0:
            quota = float(raw_quota)
            realization = (total_qty / quota) * 100.0
            if realization >= 100.0:
                quota_status = 'Pass'
                quota_pass_count += 1
            else:
                quota_status = 'Fail'
                quota_fail_count += 1
        else:
            quota = None
            realization = None
            quota_status = 'N/A'
            quota_na_count += 1

        rows.append({
            'product_id': pid,
            'item': rec['item'],
            'category': cat,
            'uom': rec['uom'],
            'total_qty': total_qty,
            'month_qtys': [rec['month_qtys'][m] for m in month_nums],
            'subtotal_amount': subtotal,
            'comm_rate': rec['comm_rate'],
            'commission_amount': comm_amt,
            'avg_selling_price': asp,
            'wholesale_price': wp,
            'missing_wholesale_price': missing_wp,
            'evaluation': evaluation,
            'quota': quota,
            'realization': realization,
            'quota_status': quota_status,
        })

    rows.sort(key=lambda r: ((r['category'] or '').lower(), (r['item'] or '').lower()))

    total_products = len(rows)
    above_bm_rate = (above_bm_count / float(total_products) * 100.0) if total_products else 0.0

    category_totals = [
        {'category': k, 'amount': v}
        for k, v in sorted(category_totals_map.items(), key=lambda kv: kv[0].lower())
    ]

    return {
        'summary': {
            'agent': agent_name or '',
            'period': period_label,
            'total_amount': total_amount,
            'category_totals': category_totals,
            'commission_total': commission_total,
            'commission_paid': commission_paid,
            'commission_unpaid': commission_unpaid,
            'above_bm_count': above_bm_count,
            'below_bm_count': below_bm_count,
            'no_sale_count': no_sale_count,
            'missing_wp_count': missing_wp_count,
            'total_products': total_products,
            'above_bm_rate': above_bm_rate,
            'quota_pass_count': quota_pass_count,
            'quota_fail_count': quota_fail_count,
            'quota_na_count': quota_na_count,
        },
        'month_columns': month_columns,
        'rows': rows,
    }
