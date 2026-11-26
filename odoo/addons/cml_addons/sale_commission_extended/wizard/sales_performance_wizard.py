# -*- coding: utf-8 -*-
from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ..reports.commission_report_data import _format_commission_rate
from ..reports.sales_performance_data import (
    compute_sales_performance,
    get_period_bounds,
)


class SalesPerformanceWizard(models.TransientModel):
    _name = 'sale.commission.sales.performance.wizard'
    _description = 'Sales Performance Report Wizard'

    def _default_wholesale_pricelist(self):
        return self.env['product.pricelist'].search(
            [('is_wholesale_pricelist', '=', True)], limit=1
        )

    def _default_quarter(self):
        return str((date.today().month - 1) // 3 + 1)

    agent_id = fields.Many2one(
        'res.partner',
        string='Sales Agent',
        domain=[('agent', '=', True)],
        required=True,
    )
    period_type = fields.Selection(
        [('quarter', 'Quarterly'), ('month', 'Monthly')],
        string='Period Type',
        default='quarter',
        required=True,
    )
    year = fields.Integer(
        string='Year',
        default=lambda self: date.today().year,
        required=True,
    )
    quarter = fields.Selection(
        [
            ('1', 'Q1 (Jan - Mar)'),
            ('2', 'Q2 (Apr - Jun)'),
            ('3', 'Q3 (Jul - Sep)'),
            ('4', 'Q4 (Oct - Dec)'),
        ],
        string='Quarter',
        default=_default_quarter,
    )
    month = fields.Selection(
        [
            ('1', 'January'), ('2', 'February'), ('3', 'March'),
            ('4', 'April'), ('5', 'May'), ('6', 'June'),
            ('7', 'July'), ('8', 'August'), ('9', 'September'),
            ('10', 'October'), ('11', 'November'), ('12', 'December'),
        ],
        string='Month',
        default=lambda self: str(date.today().month),
    )
    pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Wholesale Price List',
        default=_default_wholesale_pricelist,
        help='Defaults to the pricelist marked "Is Wholesale Pricelist".',
    )

    def _collect_wholesale_prices(self, products):
        """Return {product_id: price} only for products matched by a pricelist rule.

        Products missing from the Wholesale Price List are omitted so the
        calculation engine shows 0.00 and flags them.
        """
        prices = {}
        if not self.pricelist_id or not products:
            return prices
        # Odoo 12 _compute_price_rule returns {product_id: (price, rule_id)}
        # rule_id is False when no rule in the pricelist matched the product.
        args = [(p, 1.0, self.agent_id) for p in products]
        rule_results = self.pricelist_id._compute_price_rule(args)
        for p in products:
            price, rule_id = rule_results.get(p.id, (0.0, False))
            if rule_id:
                prices[p.id] = price
        return prices

    def _collect_catalog_products(self):
        """Collect 0-sale products from the Wholesale Price List and Agent Quotas."""
        Product = self.env['product.product']
        prod_records = Product.browse()
        if self.agent_id.quota_ids:
            prod_records |= self.agent_id.quota_ids.mapped('product_id')
        if self.pricelist_id:
            for item in self.pricelist_id.item_ids:
                if item.applied_on == '0_product_variant' and item.product_id:
                    prod_records |= item.product_id
                elif item.applied_on == '1_product' and item.product_tmpl_id:
                    prod_records |= item.product_tmpl_id.product_variant_ids
        return prod_records

    def get_report_data(self):
        self.ensure_one()
        if self.period_type == 'quarter' and not self.quarter:
            raise UserError(_('Please select a Quarter.'))
        if self.period_type == 'month' and not self.month:
            raise UserError(_('Please select a Month.'))

        date_from, date_to, period_label, month_columns = get_period_bounds(
            self.period_type, self.year, quarter=self.quarter, month=self.month
        )

        # Find all posted customer invoices / credit notes in period linked to this agent
        inv_domain = [
            ('type', 'in', ('out_invoice', 'out_refund')),
            ('state', 'in', ('open', 'paid')),
            ('date_invoice', '>=', date_from),
            ('date_invoice', '<=', date_to),
        ]
        period_invoices = self.env['account.invoice'].search(inv_domain)

        # Match invoices either directly via invoice.agent_id or via commission lines
        agent_lines = self.env['account.invoice.line.agent'].search([
            ('agent', '=', self.agent_id.id),
            ('invoice', 'in', period_invoices.ids),
        ])
        categ_lines = self.env['account.invoice.line.categ'].search([
            ('agent', '=', self.agent_id.id),
            ('invoice', 'in', period_invoices.ids),
        ])

        comm_by_inv_line = {}
        for al in agent_lines:
            comm_by_inv_line.setdefault(al.object_id.id, []).append(al)
        for cl in categ_lines:
            comm_by_inv_line.setdefault(cl.object_id.id, []).append(cl)

        matched_inv_ids = set(period_invoices.filtered(lambda i: i.agent_id == self.agent_id).ids)
        matched_inv_ids.update(agent_lines.mapped('invoice').ids)
        matched_inv_ids.update(categ_lines.mapped('invoice').ids)
        matched_invoices = self.env['account.invoice'].browse(list(matched_inv_ids))

        invoice_line_dicts = []
        sold_products = self.env['product.product'].browse()

        for inv in matched_invoices:
            for il in inv.invoice_line_ids:
                if not il.product_id:
                    continue
                if getattr(il, 'display_type', False) in ('line_note', 'line_section'):
                    continue
                sold_products |= il.product_id
                c_lines = comm_by_inv_line.get(il.id, [])
                comm_amt = sum(c.amount for c in c_lines)
                rates = []
                for c in c_lines:
                    r_str = _format_commission_rate(c.commission, il.price_subtotal)
                    if r_str and r_str not in rates:
                        rates.append(r_str)
                invoice_line_dicts.append({
                    'product_id': il.product_id.id,
                    'product_name': il.product_id.display_name,
                    'category_name': il.product_id.categ_id.name if il.product_id.categ_id else 'Uncategorized',
                    'uom_name': il.uom_id.name if il.uom_id else (il.product_id.uom_id.name if il.product_id.uom_id else ''),
                    'invoice_date': inv.date_invoice,
                    'invoice_state': inv.state,
                    'invoice_type': inv.type,
                    'quantity': il.quantity,
                    'price_subtotal': il.price_subtotal,
                    'commission_amount': comm_amt,
                    'commission_rate_str': ' + '.join(rates),
                })

        catalog_prod_records = self._collect_catalog_products()
        all_products = sold_products | catalog_prod_records
        wholesale_prices = self._collect_wholesale_prices(all_products)

        catalog_dicts = [
            {
                'product_id': p.id,
                'product_name': p.display_name,
                'category_name': p.categ_id.name if p.categ_id else 'Uncategorized',
                'uom_name': p.uom_id.name if p.uom_id else '',
            }
            for p in catalog_prod_records
        ]

        quota_map = {q.product_id.id: q.quota_qty for q in self.agent_id.quota_ids}

        return compute_sales_performance(
            agent_name=self.agent_id.name,
            period_label=period_label,
            month_columns=month_columns,
            invoice_lines=invoice_line_dicts,
            catalog_products=catalog_dicts,
            wholesale_prices=wholesale_prices,
            quota_map=quota_map,
        )

    @api.multi
    def action_export_excel(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/sale_commission_extended/export_sales_performance/%s' % self.id,
            'target': 'self',
        }

    @api.multi
    def action_print_pdf(self):
        self.ensure_one()
        return self.env.ref(
            'sale_commission_extended.action_report_sales_performance'
        ).report_action(self)
