# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    has_overdue_invoices = fields.Boolean(
        string='Has Overdue Invoices',
        compute='_compute_has_overdue_invoices',
    )
    overdue_invoices_message = fields.Text(
        string='Overdue Invoices Message',
        compute='_compute_has_overdue_invoices',
    )

    @api.depends('partner_id')
    def _compute_has_overdue_invoices(self):
        today = fields.Date.context_today(self)
        Invoice = self.env['account.invoice']
        for order in self:
            overdue_invoices = Invoice.browse()
            if order.partner_id:
                overdue_invoices = Invoice.search([
                    ('partner_id', 'child_of', order.partner_id.commercial_partner_id.id),
                    ('state', '=', 'open'),
                    ('date_due', '<', today),
                    ('type', 'in', ('out_invoice', 'out_refund')),
                ])
            order.has_overdue_invoices = bool(overdue_invoices)
            if overdue_invoices:
                lines = []
                for inv in overdue_invoices:
                    lines.append(u"%s (Due: %s, Amount: %s %s)" % (
                        inv.number or _('Draft'),
                        inv.date_due,
                        inv.residual,
                        inv.currency_id.name,
                    ))
                order.overdue_invoices_message = _(
                    "This customer has %d overdue invoice(s):\n%s"
                ) % (len(overdue_invoices), "\n".join(lines))
            else:
                order.overdue_invoices_message = False

    @api.multi
    def action_confirm(self):
        for order in self:
            if order.has_overdue_invoices:
                raise UserError(_(
                    "Cannot confirm this Sales Order.\n\n%s"
                ) % order.overdue_invoices_message)
        return super(SaleOrder, self).action_confirm()
