from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    post_loan_journal_entries = fields.Boolean('Post to Journal')
    post_canteen_journal_entries = fields.Boolean('Post to Journal')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            post_loan_journal_entries=bool(self.env['ir.config_parameter'].sudo().get_param(
                'loans.post_loan_journal_entries')),
            post_canteen_journal_entries=bool(self.env['ir.config_parameter'].sudo().get_param(
                'loans.post_canteen_journal_entries'))
            )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'loans.post_loan_journal_entries', self.post_loan_journal_entries)
        self.env['ir.config_parameter'].sudo().set_param(
            'loans.post_canteen_journal_entries', self.post_canteen_journal_entries)
