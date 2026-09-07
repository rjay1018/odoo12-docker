from odoo import fields, models, api


class OfficialReceiptNumber(models.TransientModel):
    _inherit = "account.register.payments"

    official_receipt_no = fields.Char(string="OR No.")
    cheque_no = fields.Integer(string="Cheque No.")
    bank_id = fields.Many2one("res.bank", string="Bank")
    cheque_date = fields.Date(string="Cheque Date")

    @api.multi
    def create_payments(self):
        res = super(OfficialReceiptNumber, self).create_payments()
        payment = self.env['account.payment'].search([])
        for k,v in res.items():
            if k == "res_id":
                for rec in payment:
                    if rec.id == v:
                        rec.write({
                            'official_receipt_no': self.official_receipt_no,
                            'cheque_no': self.cheque_no,
                            'bank_id': self.bank_id.id,
                            'cheque_date': self.cheque_date
                        })
        return res
