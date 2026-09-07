from odoo import models, fields, api

class maintenance_purchase_order(models.Model):
    _inherit = 'purchase.order'

    maintenance_request_id = fields.Many2one(
        'maintenance.request'
    )