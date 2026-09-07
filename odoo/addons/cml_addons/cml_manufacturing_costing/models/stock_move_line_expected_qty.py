# -*- coding: utf-8 -*-


from odoo import models, api,fields


class StockMoveLineExpectedQty(models.Model):
    _inherit = 'stock.move.line'

    product_expected_qty = fields.Float(
        'Expected Qty', default=0.0,
        compute='get_expected_qty',
        copy=False, required=True)

    product_expected_uom_id = fields.Many2one(
        'uom.uom', 'Product Expected Unit of Measure',
        related='product_id.uom_id',
        readonly=True, required=True,
        states={'confirmed': [('readonly', False)]})

  
    @api.multi
    def get_expected_qty(self):
        for mo in self:
           mo.product_expected_qty = mo.product_uom_id._compute_quantity(mo.qty_done, mo.product_id.uom_id, rounding_method='HALF-UP')

    


   