# -*- coding: utf-8 -*-

from odoo import models,fields,api,exceptions,_

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}

class Invoice(models.Model):
    _inherit = 'account.invoice'

    appointment_id = fields.Many2one(
        'clinic.appointment',
        string="Appointment",
        copy=False
    )
    total_insurance_amount = fields.Float(
        "Total Insurance Amount",
        compute="_set_insurance_amount"
    )
    insurance_agency_id = fields.Many2one(
        'res.partner',
        string="Insurance Agency",
        related="partner_id.insurance_agency_id"
    )
    insur_payment_done = fields.Boolean(
        default=False,
        copy=False
    )
    # origin_id = fields.Many2one(
    #     'clinic.appointment',
    #     string='Appointment Number'
    # )

    @api.depends('invoice_line_ids.is_insurance_agency','invoice_line_ids.price_total')
    def _set_insurance_amount(self):
        for rec in self:
            amount = 0
            for l in rec.invoice_line_ids.filtered(lambda l:l.is_insurance_agency == True):
                amount += l.price_total
            rec.total_insurance_amount = amount

    @api.multi
    def write(self, vals):
        state = vals.get('state')
        if state == 'cancel':
            for rec in self:
                if rec.appointment_id:
                    rec.appointment_id.show_create_invoice = True
        return super(Invoice, self).write(vals)

class Invoice_lines(models.Model):
    _inherit = 'account.invoice.line'

    is_insurance_agency = fields.Boolean(
        "is Insurance Agency",
        default = False
    )

class account_register_payments_multi(models.TransientModel):
    _inherit = "account.register.payments"

    @api.multi
    def create_payments(self):
        inv_ = self.invoice_ids.filtered(lambda l: l.partner_id.insurance_agency_id)
        if inv_:
            insurance_agency_id = inv_[0].partner_id.insurance_agency_id.id
            for rec in self.invoice_ids:
                if rec.partner_id.insurance_agency_id.id != insurance_agency_id:
                    raise exceptions.UserError(_("Insurance Agency Must be same for all Invoice"))
        call_super = super(account_register_payments_multi, self).create_payments()
        return call_super

    @api.multi
    def get_payments_vals(self):
        inv_ = self.invoice_ids.filtered(lambda l: l.partner_id.insurance_agency_id)
        if inv_ and len(self.invoice_ids) > 0:
            return [self._prepare_payment_vals_new(self.invoice_ids)]
        call_super = super(account_register_payments_multi, self).get_payments_vals()
        return call_super

    @api.multi
    def _prepare_payment_vals_new(self, invoices):
        amount = self._compute_payment_amount(invoices=invoices)
        payment_type = self.payment_type
        bank_account = self.partner_bank_account_id
        pmt_communication = self._prepare_communication(invoices)
        partner_id = invoices[0].partner_id.insurance_agency_id

        values = {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': pmt_communication,
            'invoice_ids': [(6, 0, invoices.ids)],
            'payment_type': payment_type,
            'amount': abs(amount),
            'currency_id': self.currency_id.id,
            'partner_id': partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            'partner_bank_account_id': bank_account.id,
            'multi': False,
            'payment_difference_handling': self.payment_difference_handling,
            'writeoff_account_id': self.writeoff_account_id.id,
            'writeoff_label': self.writeoff_label,
        }

        return values