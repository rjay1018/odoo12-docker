# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models, api


class InvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    state = fields.Selection(related="invoice_id.state",
                             string="State", store=True)
    inv_type = fields.Selection(
        related="invoice_id.type", string="Type", store=True)

    image = fields.Binary(string=" ",
                          compute='_compute_image'
                          )

    category_id = fields.Many2one('product.category',
        # related="product_id.categ_id",
                             string="Product Category", store=True)

    invoice_date = fields.Date(related="invoice_id.date_invoice",string="Invoice Date", store=True)


    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(InvoiceLine, self)._onchange_product_id()
        self.category_id = self.product_id.categ_id
        return res

    def _compute_image(self):
        """Get the image from the template if no image is set on the variant."""
        for record in self:
            record.image = record.product_id.image_variant or record.product_id.product_tmpl_id.image
