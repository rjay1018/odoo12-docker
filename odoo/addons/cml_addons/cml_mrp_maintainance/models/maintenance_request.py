from odoo import fields, models, api, _


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    production_id = fields.Many2one(
        'mrp.production',
        string="Manufacturing Order"
    )

    workorder_id = fields.Many2one(
        'mrp.workorder',
        string="Work Order"
    )
