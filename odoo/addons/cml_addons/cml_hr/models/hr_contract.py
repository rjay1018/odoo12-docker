from odoo import fields, models, api


class HrContract (models.Model):
    _inherit = 'hr.contract'

    @api.multi
    def _compute_amount_in_word(self):
        for rec in self:
            rec.num_word = str(rec.currency_id.amount_to_text(rec.wage))

    num_word = fields.Char(string="Amount In Words:", compute='_compute_amount_in_word')
    daily_rate = fields.Float(string="Daily Rate")
    hourly_rate = fields.Float(string="Hourly Rate")
