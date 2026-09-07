# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.


from odoo import models, fields, api

class StockMove(models.Model):
    _inherit = "stock.move"

    sh_pol_picking_order_line_picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        related="picking_id.picking_type_id",
        ondelete='set null',
        store=True,
        string="Picking Type",
    )

    sh_pol_picking_order_line_picking_type_code = fields.Selection(
        related="picking_id.picking_type_id.code",
        store=True,
        string="Picking Operation",
    )

    image = fields.Binary(string=" ",
                          compute='_compute_image')

    category_id = fields.Many2one('product.category',
        # related="product_id.categ_id",
                             string="Product Category", store=True)


    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(StockMove, self).onchange_product_id()
        self.category_id = self.product_id.categ_id
        return res

    def _compute_image(self):
        """Get the image from the template if no image is set on the variant."""
        for record in self:
            record.image = record.product_id.image_variant or record.product_id.product_tmpl_id.image


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    sh_pol_picking_order_line_picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        related="picking_id.picking_type_id",
        ondelete='set null',
        store=True,
        string="Picking Type",
    )

    sh_pol_picking_order_line_picking_type_code = fields.Selection(
        related="picking_id.picking_type_id.code",
        store=True,
        string="Picking Operation",
    )
    sh_pol_picking_order_line_origin = fields.Char(
        related="picking_id.origin",
        store=True,
    )

    image = fields.Binary(
        string=" ",
        compute='_compute_image')

    category_id = fields.Many2one(
        'product.category',
        #related="product_id.categ_id",
        string="Product Category",
        store=True )

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(StockMoveLine, self).onchange_product_id()
        self.category_id = self.product_id.categ_id
        return res

    def _compute_image(self):
        """Get the image from the template if no image is set on the variant."""
        for record in self:
            record.image = record.product_id.image_variant or record.product_id.product_tmpl_id.image
