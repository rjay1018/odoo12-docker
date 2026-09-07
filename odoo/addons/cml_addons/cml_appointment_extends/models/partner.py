from odoo import models,fields,api

class Res_partn(models.Model):
    _inherit = 'res.partner'

    insurance_agency_id = fields.Many2one(
        'res.partner',
        string="Insurance Agency",
    )
    is_respondent = fields.Boolean(
        string="respondent"
    )