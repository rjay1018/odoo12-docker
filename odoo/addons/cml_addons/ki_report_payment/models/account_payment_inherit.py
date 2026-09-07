from odoo import api, fields, models, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    report_ids = fields.Many2many('ir.actions.report', string="Report", copy=False)
