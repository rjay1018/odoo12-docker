# -*- coding: utf-8 -*-
import datetime
import unittest
from types import SimpleNamespace

from ..reports.commission_report_data import (
    _format_commission_rate,
    get_by_customer_data,
    get_by_invoice_data,
)


def _make_line(
    inv_line_id,
    invoice_id,
    inv_number,
    inv_date,
    partner_id,
    partner_name,
    product_name,
    qty,
    price_unit,
    price_subtotal,
    settled_amount,
    commission,
    inv_type='out_invoice',
    agent_name='Agent TY',
    uom_name='Box',
):
    partner = SimpleNamespace(id=partner_id, name=partner_name)
    invoice = SimpleNamespace(
        id=invoice_id,
        number=inv_number,
        name='',
        date_invoice=inv_date,
        partner_id=partner,
        type=inv_type,
    )
    inv_line = SimpleNamespace(
        id=inv_line_id,
        invoice_id=invoice,
        product_id=SimpleNamespace(id=inv_line_id * 10, name=product_name),
        uom_id=SimpleNamespace(name=uom_name),
        quantity=qty,
        price_unit=price_unit,
        price_subtotal=price_subtotal,
    )
    return SimpleNamespace(
        invoice_line=inv_line,
        invoice=invoice,
        date=inv_date,
        commission=commission,
        settled_amount=settled_amount,
        agent=SimpleNamespace(name=agent_name),
        agent_line=[],
        agent_line_categ=[],
    )


class TestCommissionReports(unittest.TestCase):

    def setUp(self):
        self.comm_pct = SimpleNamespace(name='1.5% Comm', commission_type='pct', fix_qty=1.5)
        self.comm_fix = SimpleNamespace(name='Fixed 50', commission_type='fix', fix_qty=50.0)
        self.comm_sec = SimpleNamespace(
            name='Tiered',
            commission_type='section',
            fix_qty=0.0,
            sections=[
                SimpleNamespace(amount_from=0, amount_to=1000, percent=1.0),
                SimpleNamespace(amount_from=1000.01, amount_to=10000, percent=2.5),
            ],
        )

    def test_format_commission_rate(self):
        self.assertEqual(_format_commission_rate(self.comm_pct, 500.0), '1.5%')
        self.assertEqual(_format_commission_rate(self.comm_fix, 500.0), 'Fixed (50.00)')
        self.assertEqual(_format_commission_rate(self.comm_sec, 500.0), '1%')
        self.assertEqual(_format_commission_rate(self.comm_sec, 2500.0), '2.5%')
        self.assertEqual(_format_commission_rate(self.comm_sec, 99999.0), 'Tiered')
        self.assertEqual(_format_commission_rate(None, 500.0), '')

    def test_by_customer_grouping_and_refund_subtraction(self):
        lines = [
            _make_line(
                1, 10, 'INV/2026/0001', datetime.date(2026, 7, 10),
                100, 'Beta Foods', 'Tapioca Pearl', 10.0, 100.0, 1000.0, 15.0, self.comm_pct,
            ),
            _make_line(
                2, 11, 'RINV/2026/0001', datetime.date(2026, 7, 12),
                100, 'Beta Foods', 'Tapioca Pearl', 2.0, 100.0, 200.0, -3.0, self.comm_pct,
                inv_type='out_refund',
            ),
            _make_line(
                3, 12, 'INV/2026/0002', datetime.date(2026, 7, 5),
                200, 'Alpha Tea', 'Green Tea', 5.0, 200.0, 1000.0, 250.0, self.comm_fix,
            ),
        ]
        settlement = SimpleNamespace(
            agent=SimpleNamespace(name='Agent TY'),
            lines=lines,
            categ_lines=[],
        )

        data = get_by_customer_data(settlement)
        # Sorted alphabetically by customer: Alpha Tea, then Beta Foods
        self.assertEqual([c['partner'] for c in data['customers']], ['Alpha Tea', 'Beta Foods'])

        alpha = data['customers'][0]
        self.assertAlmostEqual(alpha['total_sales'], 1000.0)
        self.assertAlmostEqual(alpha['total_commission'], 250.0)

        beta = data['customers'][1]
        self.assertEqual(len(beta['lines']), 2)
        self.assertAlmostEqual(beta['lines'][1]['quantity'], -2.0)
        self.assertAlmostEqual(beta['lines'][1]['price_subtotal'], -200.0)
        self.assertAlmostEqual(beta['total_sales'], 800.0)
        self.assertAlmostEqual(beta['total_commission'], 12.0)

        self.assertAlmostEqual(data['grand_total_sales'], 1800.0)
        self.assertAlmostEqual(data['grand_total_commission'], 262.0)

    def test_by_invoice_grouping_and_deduplication(self):
        # Two commission lines hitting the SAME invoice line (id=1) should not double-count sales
        line_a = _make_line(
            1, 10, 'INV/2026/0001', datetime.date(2026, 7, 10),
            100, 'Beta Foods', 'Tapioca Pearl', 10.0, 100.0, 1000.0, 15.0, self.comm_pct,
        )
        line_b = _make_line(
            1, 10, 'INV/2026/0001', datetime.date(2026, 7, 10),
            100, 'Beta Foods', 'Tapioca Pearl', 10.0, 100.0, 1000.0, 50.0, self.comm_fix,
        )
        line_c = _make_line(
            2, 12, 'INV/2026/0002', datetime.date(2026, 7, 5),
            200, 'Alpha Tea', 'Green Tea', 5.0, 200.0, 1000.0, 25.0, self.comm_sec,
        )
        settlement = SimpleNamespace(
            agent=SimpleNamespace(name='Agent TY'),
            lines=[line_a, line_c],
            categ_lines=[line_b],
        )

        data = get_by_invoice_data(settlement)
        # Sorted by date: INV/2026/0002 (Jul 5), then INV/2026/0001 (Jul 10)
        self.assertEqual([i['invoice'] for i in data['invoices']], ['INV/2026/0002', 'INV/2026/0001'])

        inv1 = data['invoices'][1]
        self.assertEqual(inv1['partner'], 'Beta Foods')
        self.assertEqual(inv1['agent'], 'Agent TY')
        self.assertEqual(len(inv1['lines']), 1)
        self.assertAlmostEqual(inv1['total_sales'], 1000.0)
        self.assertAlmostEqual(inv1['total_commission'], 65.0)
        self.assertEqual(inv1['lines'][0]['commission_rate'], '1.5% + Fixed (50.00)')

        self.assertAlmostEqual(data['grand_total_sales'], 2000.0)
        self.assertAlmostEqual(data['grand_total_commission'], 90.0)
