from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_apply_free_session = fields.Boolean(
        string='Give Free Session?',
    )
    free_session_number = fields.Integer(
        string='Free Sessions',
    )
    free_product_id = fields.Many2one(
        'product.product',
        string='Free Session Product',
    )

    allow_free_session_product_ids = fields.Many2many(
        'product.product',
        string="Allowed Free Sessions"
    )
