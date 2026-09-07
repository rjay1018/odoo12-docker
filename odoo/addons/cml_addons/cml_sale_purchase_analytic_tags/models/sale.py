# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        result = super(SaleOrderLine, self).product_id_change()
        if not self.product_id:
            return result
        if self.product_id.sale_analytic_tag_ids:
            self.update({
                'analytic_tag_ids': [(6, 0, self.product_id.sale_analytic_tag_ids.ids)]
            })
        return result
