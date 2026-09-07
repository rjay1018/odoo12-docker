from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    requested_by = fields.Char(
        string='Requested By',
    )
    