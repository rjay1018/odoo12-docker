# -*- coding: utf-8 -*-

from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, float_is_zero, pycompat

import logging
_logger = logging.getLogger(__name__)



class StockMoveLineExpectedQty(models.Model):
    _inherit = 'stock.move'

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
           mo.product_expected_qty = mo.product_uom._compute_quantity(mo.quantity_done, mo.product_id.uom_id, rounding_method='HALF-UP') 

    def _get_price_unit(self):
        """ Returns the unit price to store on the quant """
        price_unit = super(StockMoveLineExpectedQty, self)._get_price_unit()
        if self.product_id.cost_method == 'standard' and  self.product_id.categ_id.cost_from_mo:
            if self.production_id and self.production_id.product_unit_cost: 
                price_unit = self.production_id.product_unit_cost
        return price_unit

    @api.multi
    def product_price_update_before_done(self, forced_qty=None):
        super_res = super(StockMoveLineExpectedQty, self).product_price_update_before_done(forced_qty)
        for move in self.filtered(lambda move: move._is_in() and move.product_id.cost_method == 'standard'):
            if move.product_id.categ_id.cost_from_mo:
                if move.production_id and move.production_id.product_unit_cost:
                    new_std_price = move.production_id.product_unit_cost
                    move.product_id.with_context(force_company=move.company_id.id).sudo().write({'standard_price': new_std_price})
        return super_res
