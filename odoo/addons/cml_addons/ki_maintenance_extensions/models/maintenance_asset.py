from odoo import models, fields, api

class maintenance_asset(models.Model):

    _inherit = 'account.asset.asset'

    maintenance_equipment_id = fields.Many2one(
        'maintenance.equipment',
        string="Equipment",
        readonly=True
    )
