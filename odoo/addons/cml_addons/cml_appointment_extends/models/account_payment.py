from odoo import models,fields,api,_
from odoo.exceptions import UserError


class acc_Payment(models.Model):
    _inherit = 'account.payment'

    is_insurance_agency = fields.Boolean(
        "By Insurance Agency",
        default = False,
        copy=False
    )
    agen_invoice_ids = fields.Many2many(
        'account.invoice', 'account_invoice_payment_rel_new', 'partner_id', 'invoice_id',
        copy=False
    )

    payment_notes = fields.Text(
        string='Payment Notes'
    )

    @api.onchange('partner_id','is_insurance_agency')
    def set_invoices(self):
        for rec in self:
            rec.agen_invoice_ids = [(6,0,[])]
            if rec.partner_id:
                if rec.is_insurance_agency:
                    inv_ids = self.env['account.invoice'].sudo().search([('insurance_agency_id','=',rec.partner_id.id),('state','not in',['draft','cancel']),('residual','>',0),('total_insurance_amount','>',0),('insur_payment_done','=',False)])
                    rec.agen_invoice_ids = [(6, 0, inv_ids.ids)]
                    rec.amount = sum(self.agen_invoice_ids.mapped('total_insurance_amount'))
                else:
                    inv_ids = self.env['account.invoice'].sudo().search(
                        [('partner_id', '=', rec.partner_id.id), ('state', 'not in', ['draft', 'cancel']),
                         ('residual', '>', 0)])
                    rec.agen_invoice_ids = [(6, 0, inv_ids.ids)]
                    rec.amount = sum(self.agen_invoice_ids.mapped('residual'))

    @api.multi
    def post(self):
        for rec in self:
            if rec.agen_invoice_ids:
                if rec.amount < sum(rec.agen_invoice_ids.mapped('residual')) and not rec.is_insurance_agency:
                    raise UserError(
                        _("The sum of the Residual amount of listed invoices are greater than payment's amount."))
                elif rec.amount < sum(rec.agen_invoice_ids.mapped('total_insurance_amount')) and rec.is_insurance_agency:
                    raise UserError(
                        _("The sum of the Insurance amount of listed invoices are greater than payment's amount."))
        res = super(acc_Payment, self).post()
        return res

    def _create_payment_entry(self, amount):
        """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
            Return the journal entry.
        """
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)

        move = self.env['account.move'].create(self._get_move_vals())

        counterpart_aml_list = {}
        # Write line corresponding to invoice payment
        if self.agen_invoice_ids and self.payment_type == 'inbound':
            total_reconcile_amount = 0.00
            total_separate_amount_currency = 0.00
            for payment_invoice_id in self.agen_invoice_ids:
                reconcile_amount_new = payment_invoice_id.total_insurance_amount if self.is_insurance_agency and (payment_invoice_id.residual-payment_invoice_id.total_insurance_amount >= 0) else payment_invoice_id.residual if not self.is_insurance_agency else 0
                if reconcile_amount_new > 0:
                    separate_amount_currency = amount_currency
                    reconcile_amount = reconcile_amount_new
                    if amount_currency and credit:
                        reconcile_amount = (reconcile_amount_new * credit) / amount_currency
                        separate_amount_currency = -reconcile_amount_new
                        reconcile_amount = -reconcile_amount
                    total_reconcile_amount += reconcile_amount
                    total_separate_amount_currency += separate_amount_currency
                    counterpart_aml_dict = self._get_shared_move_line_vals(debit, reconcile_amount, separate_amount_currency, move.id, False)
                    counterpart_aml_dict.update(self._get_counterpart_move_line_vals([payment_invoice_id]))
                    counterpart_aml_dict.update({'currency_id': currency_id})
                    counterpart_aml = aml_obj.create(counterpart_aml_dict)
                    counterpart_aml_list[payment_invoice_id.id] = counterpart_aml
            if credit > total_reconcile_amount:
                remaining_reconcile_amount = credit - total_reconcile_amount
                separate_amount_currency = amount_currency
                if amount_currency and credit:
                    separate_amount_currency = amount_currency - total_separate_amount_currency
                counterpart_aml_dict = self._get_shared_move_line_vals(debit, remaining_reconcile_amount, separate_amount_currency, move.id, False)
                counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
                counterpart_aml_dict.update({'currency_id': currency_id})
                counterpart_aml = aml_obj.create(counterpart_aml_dict)
        elif self.agen_invoice_ids and self.payment_type == 'outbound':
            total_reconcile_amount = 0.00
            total_separate_amount_currency = 0.00
            for payment_invoice_id in self.agen_invoice_ids:
                reconcile_amount_new = payment_invoice_id.total_insurance_amount if self.is_insurance_agency and (payment_invoice_id.residual-payment_invoice_id.total_insurance_amount >= 0) else payment_invoice_id.residual if not self.is_insurance_agency else 0
                if reconcile_amount_new > 0:
                    separate_amount_currency = amount_currency
                    reconcile_amount = reconcile_amount_new
                    if amount_currency and debit:
                        reconcile_amount = (reconcile_amount_new * debit) / amount_currency
                        separate_amount_currency = reconcile_amount_new
                    total_reconcile_amount += reconcile_amount
                    total_separate_amount_currency += separate_amount_currency
                    counterpart_aml_dict = self._get_shared_move_line_vals(reconcile_amount, credit, separate_amount_currency, move.id, False)
                    counterpart_aml_dict.update(self._get_counterpart_move_line_vals([payment_invoice_id]))
                    counterpart_aml_dict.update({'currency_id': currency_id})
                    counterpart_aml = aml_obj.create(counterpart_aml_dict)
                    counterpart_aml_list[payment_invoice_id.id] = counterpart_aml
            if debit > total_reconcile_amount:
                remaining_reconcile_amount = debit - total_reconcile_amount
                separate_amount_currency = amount_currency
                if amount_currency and debit:
                    separate_amount_currency = amount_currency - total_separate_amount_currency
                counterpart_aml_dict = self._get_shared_move_line_vals(remaining_reconcile_amount, credit, separate_amount_currency, move.id, False)
                counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
                counterpart_aml_dict.update({'currency_id': currency_id})
                counterpart_aml = aml_obj.create(counterpart_aml_dict)
        else:
            counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
            counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
            counterpart_aml_dict.update({'currency_id': currency_id})
            counterpart_aml = aml_obj.create(counterpart_aml_dict)

        #Reconcile with the invoices
        if self.payment_difference_handling == 'reconcile' and self.payment_difference and not self.agen_invoice_ids:
            writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
            debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(self.payment_difference, self.currency_id, self.company_id.currency_id)
            writeoff_line['name'] = self.writeoff_label
            writeoff_line['account_id'] = self.writeoff_account_id.id
            writeoff_line['debit'] = debit_wo
            writeoff_line['credit'] = credit_wo
            writeoff_line['amount_currency'] = amount_currency_wo
            writeoff_line['currency_id'] = currency_id
            writeoff_line = aml_obj.create(writeoff_line)
            if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
                counterpart_aml['debit'] += credit_wo - debit_wo
            if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
                counterpart_aml['credit'] += debit_wo - credit_wo
            counterpart_aml['amount_currency'] -= amount_currency_wo

        #Write counterpart lines
        if not self.currency_id.is_zero(self.amount):
            if not self.currency_id != self.company_id.currency_id:
                amount_currency = 0
            liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
            liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
            aml_obj.create(liquidity_aml_dict)

        #validate the payment
        if not self.journal_id.post_at_bank_rec:
            move.post()

        #reconcile the invoice receivable/payable line(s) with the payment
        if self.agen_invoice_ids and self.payment_type in ['inbound', 'outbound']:
            invoice_ids = []
            for counterpart_aml_list_itr in counterpart_aml_list.keys():
                invoice_obj = self.env['account.invoice'].browse([counterpart_aml_list_itr])
                invoice_ids.append(counterpart_aml_list_itr)
                invoice_obj.register_payment(counterpart_aml_list[counterpart_aml_list_itr])
                if self.is_insurance_agency:
                    invoice_obj.insur_payment_done = True
            self.invoice_ids = [(6, 0, invoice_ids)]
        else:
            self.invoice_ids.register_payment(counterpart_aml)

        return move