# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        result = super(PurchaseOrderLine, self).onchange_product_id()
        if not self.product_id:
            return result
        if self.product_id.purchase_analytic_tag_ids:
            self.update({
                'analytic_tag_ids': [(6, 0, self.product_id.purchase_analytic_tag_ids.ids)]
            })
        return result
