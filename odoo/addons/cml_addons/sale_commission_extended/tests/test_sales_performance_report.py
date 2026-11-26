# -*- coding: utf-8 -*-
import datetime
import unittest

from ..reports.sales_performance_data import (
    compute_sales_performance,
    get_period_bounds,
)


class TestSalesPerformanceReport(unittest.TestCase):

    def test_period_bounds_quarterly_and_monthly(self):
        d1, d2, label, cols = get_period_bounds('quarter', 2026, quarter=3)
        self.assertEqual(d1, datetime.date(2026, 7, 1))
        self.assertEqual(d2, datetime.date(2026, 9, 30))
        self.assertEqual(label, '3RD 2026')
        self.assertEqual(cols, [(7, 'Jul'), (8, 'Aug'), (9, 'Sep')])

        d1, d2, label, cols = get_period_bounds('month', 2024, month=2)
        self.assertEqual(d1, datetime.date(2024, 2, 1))
        self.assertEqual(d2, datetime.date(2024, 2, 29))  # leap year
        self.assertEqual(label, 'FEB 2024')
        self.assertEqual(cols, [(2, 'Feb')])

    def test_evaluation_refunds_quotas_and_summary(self):
        _, _, period_label, month_cols = get_period_bounds('quarter', 2026, quarter=3)

        invoice_lines = [
            # Product 1: Below BM (ASP = 1400 < WP 1600), Paid, Fail quota (10 / 20 = 50%)
            {
                'product_id': 1,
                'product_name': '[0101-B] Tapioca Pearl',
                'category_name': 'Tapioca Pearls',
                'uom_name': 'Box',
                'invoice_date': datetime.date(2026, 7, 15),
                'invoice_state': 'paid',
                'invoice_type': 'out_invoice',
                'quantity': 12.0,
                'price_subtotal': 16800.0,
                'commission_amount': 252.0,
                'commission_rate_str': '1.5%',
            },
            # Credit note on Product 1 in August (-2 qty, -2800 sales, -42 comm)
            {
                'product_id': 1,
                'product_name': '[0101-B] Tapioca Pearl',
                'category_name': 'Tapioca Pearls',
                'uom_name': 'Box',
                'invoice_date': datetime.date(2026, 8, 5),
                'invoice_state': 'paid',
                'invoice_type': 'out_refund',
                'quantity': 2.0,
                'price_subtotal': 2800.0,
                'commission_amount': -42.0,
                'commission_rate_str': '1.5%',
            },
            # Product 2: Above BM (ASP = 500 >= WP 450), Open (Unpaid), Pass quota (10 / 10 = 100%)
            {
                'product_id': 2,
                'product_name': '[0201-T] Black Tea',
                'category_name': 'Tea/Powder/Syrup/Sinkers',
                'uom_name': 'Box',
                'invoice_date': datetime.date(2026, 9, 10),
                'invoice_state': 'open',
                'invoice_type': 'out_invoice',
                'quantity': 10.0,
                'price_subtotal': 5000.0,
                'commission_amount': 100.0,
                'commission_rate_str': '2%',
            },
            # Product 4: Missing wholesale price, no quota -> Flagged & N/A
            {
                'product_id': 4,
                'product_name': '[0901-X] Styro Box',
                'category_name': 'Packaging',
                'uom_name': 'Pc',
                'invoice_date': datetime.date(2026, 7, 20),
                'invoice_state': 'paid',
                'invoice_type': 'out_invoice',
                'quantity': 5.0,
                'price_subtotal': 500.0,
                'commission_amount': 5.0,
                'commission_rate_str': '1%',
            },
        ]

        # Product 3: In Wholesale Price List with 0 sales -> must show 'No Sale'
        catalog_products = [
            {
                'product_id': 3,
                'product_name': '[0202-G2] Wanwan Green Tea',
                'category_name': 'Tea/Powder/Syrup/Sinkers',
                'uom_name': 'Box',
            },
        ]

        wholesale_prices = {1: 1600.0, 2: 450.0, 3: 330.37}
        quota_map = {1: 20.0, 2: 10.0, 3: 20.0}

        result = compute_sales_performance(
            agent_name='TY',
            period_label=period_label,
            month_columns=month_cols,
            invoice_lines=invoice_lines,
            catalog_products=catalog_products,
            wholesale_prices=wholesale_prices,
            quota_map=quota_map,
        )

        s = result['summary']
        self.assertEqual(s['agent'], 'TY')
        self.assertEqual(s['period'], '3RD 2026')
        self.assertAlmostEqual(s['total_amount'], 19500.0)
        # Category subtotals MUST equal total_amount
        self.assertAlmostEqual(sum(c['amount'] for c in s['category_totals']), s['total_amount'])
        self.assertAlmostEqual(s['commission_total'], 315.0)
        self.assertAlmostEqual(s['commission_paid'], 215.0)
        self.assertAlmostEqual(s['commission_unpaid'], 100.0)
        self.assertEqual(s['above_bm_count'], 1)
        self.assertEqual(s['below_bm_count'], 1)
        self.assertEqual(s['no_sale_count'], 1)
        self.assertEqual(s['missing_wp_count'], 1)
        self.assertAlmostEqual(s['above_bm_rate'], 25.0)
        self.assertEqual(s['quota_pass_count'], 1)
        self.assertEqual(s['quota_fail_count'], 2)  # Product 1 (50%) and Product 3 (0%)
        self.assertEqual(s['quota_na_count'], 1)    # Product 4 (no quota)

        by_pid = {r['product_id']: r for r in result['rows']}
        # Product 1: 12 in Jul - 2 in Aug = 10 total; monthly split sums to total
        self.assertEqual(by_pid[1]['month_qtys'], [12.0, -2.0, 0.0])
        self.assertAlmostEqual(sum(by_pid[1]['month_qtys']), by_pid[1]['total_qty'])
        self.assertAlmostEqual(by_pid[1]['avg_selling_price'], 1400.0)
        self.assertEqual(by_pid[1]['evaluation'], 'Below BM')
        self.assertAlmostEqual(by_pid[1]['realization'], 50.0)
        self.assertEqual(by_pid[1]['quota_status'], 'Fail')

        # Product 3: 0 sales -> No Sale (never wrongly Above BM)
        self.assertEqual(by_pid[3]['evaluation'], 'No Sale')
        self.assertAlmostEqual(by_pid[3]['avg_selling_price'], 0.0)

        # Product 4: Missing wholesale price & N/A quota
        self.assertTrue(by_pid[4]['missing_wholesale_price'])
        self.assertEqual(by_pid[4]['evaluation'], 'No Wholesale Price')
        self.assertIsNone(by_pid[4]['quota'])
        self.assertIsNone(by_pid[4]['realization'])
        self.assertEqual(by_pid[4]['quota_status'], 'N/A')
