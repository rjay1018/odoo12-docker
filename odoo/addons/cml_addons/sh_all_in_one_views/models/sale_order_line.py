# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models, api


class QuotationOrderLine(models.Model):
    _inherit = 'sale.order.line'

    so_order_date = fields.Datetime(
        related="order_id.date_order", string="Date Order")
    so_state = fields.Selection(
        related="order_id.state", string="State", store=True)

    image = fields.Binary(
        string=" ",
        compute='_compute_image'
        )

    category_id = fields.Many2one(
        'product.category',
        # related="product_id.categ_id",
        string="Product Category",
        store=True)

    @api.onchange('product_id')
    def product_id_change(self):
        res = super(QuotationOrderLine, self).product_id_change()
        self.category_id = self.product_id.categ_id
        return res

    def _compute_image(self):
        """Get the image from the template if no image is set on the variant."""
        for record in self:
            record.image = record.product_id.image_variant or record.product_id.product_tmpl_id.image
