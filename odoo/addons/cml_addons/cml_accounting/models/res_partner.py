from odoo import fields, models, api
from ast import literal_eval


class ResPartnerAccountStatement(models.Model):
    _inherit = 'res.partner'

    total_debits = fields.Float(
        string='Total Debit',
        compute='_get_total_debits'
    )

    total_debits_supplier = fields.Float(
        string='Total Debit',
        compute='_get_total_debits_sup'
    )

    total_credits = fields.Float(
        string='Total Credit',
        compute='_get_total_credits'
    )

    total_credits_supplier = fields.Float(
        string='Total Credit',
        compute='_get_total_credits_sup'
    )
    total_customer_invoice_count = fields.Integer(compute='_compute_total_customer_invoice_count', string='Customer Count')

    @api.depends('balance_invoice_ids')
    def _compute_total_customer_invoice_count(self):
        for rec in self:
            l = []
            for re in rec.balance_invoice_ids:
                l.append(re.id)
            rec.total_customer_invoice_count = len(l)




    @api.multi
    def _get_total_debits(self):
        total = 0
        for r in self:
            r.total_debits = sum(i.credit_amount for i in r.balance_invoice_ids)

    @api.multi
    def _get_total_debits_sup(self):
        total = 0
        for r in self:
            r.total_debits_supplier = sum(i.credit_amount for i in r.supplier_invoice_ids)

    @api.multi
    def _get_total_credits(self):
        total = 0
        for r in self:
            r.total_credits = sum(i.credit_amount for i in r.balance_invoice_ids)

    @api.multi
    def _get_total_credits_sup(self):
        total = 0
        for r in self:
            r.total_credits_supplier = sum(i.credit_amount for i in r.supplier_invoice_ids)
