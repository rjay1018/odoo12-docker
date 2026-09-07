from odoo import models, fields, api, _

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    categ_id = fields.Many2one('product.category', 'Category')

    @api.onchange('product_id')
    def onchange_product(self):
        res = super(AccountInvoiceLine, self)._onchange_product_id()
        if self.product_id:
            if self.product_id.categ_id.id != self.categ_id.id:
                self.categ_id = self.product_id.categ_id.id
        return res
