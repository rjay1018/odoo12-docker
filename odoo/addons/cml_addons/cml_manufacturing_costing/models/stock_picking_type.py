# -*- coding: utf-8 -*-
from odoo import models, api, fields, _


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'


    show_expect_qty = fields.Boolean(
        string="Show Expect qty"
    )


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    show_expect_qty = fields.Boolean(
        string="Show Expect qty",
        related='picking_type_id.show_expect_qty'
    )
