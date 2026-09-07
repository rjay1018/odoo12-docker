from odoo import api, fields, models

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    amount_in_word_ph = fields.Char(
        string="Amount in Words (PH)",
        compute="_compute_amount_in_words_ph",
        store=True
    )

    @api.depends('amount')
    def _compute_amount_in_words_ph(self):
        helper = self.env['amount.to.words.ph']
        for rec in self:
            rec.amount_in_word_ph = helper.to_words(rec.amount) if rec.amount else ""

    @api.onchange('amount')
    def _onchange_amount(self):
        self._compute_amount_in_words_ph()

