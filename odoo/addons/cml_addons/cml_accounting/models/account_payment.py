from odoo import fields, models, api


class AccountPaymentLocalization(models.Model):
    _inherit = "account.payment"

    official_receipt_no = fields.Char(
        string="OR No.",
        states={'draft': [('readonly', False)]}
    )

    cheque_no = fields.Integer(string="Cheque No.", store=True)
    bank_id = fields.Many2one("res.bank", string="Bank")
    cheque_date = fields.Date(string="Cheque Date")
    passbook = fields.Boolean('Passbook')