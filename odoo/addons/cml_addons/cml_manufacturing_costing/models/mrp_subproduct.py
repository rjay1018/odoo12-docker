# -*- coding: utf-8 -*-

from odoo import models, api,fields


class MrpSubProduct(models.Model):
    _inherit = 'mrp.subproduct'


    product_percentage = fields.Float(
        'Product Percentage',
        default=0.0)


    @api.onchange('product_percentage')
    def _onchange_product_percentage(self):
        self.product_qty = (self.product_percentage *self.bom_id.product_qty)/ 100
   