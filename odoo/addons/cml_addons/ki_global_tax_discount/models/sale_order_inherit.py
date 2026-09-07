from odoo import api, fields, models, _


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    global_tax_ids = fields.Many2many(
        'account.tax',
        string='Taxes',
    )

    global_discount = fields.Float(
        string='Discount'
    )


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _compute_tax_id(self):
        res = super(SaleOrderLineInherit, self)._compute_tax_id()
        for rec in self:
            if rec.order_id.global_tax_ids:
                rec.tax_id = rec.order_id.global_tax_ids
            if rec.order_id.global_discount:
                rec.discount = rec.order_id.global_discount
        return res
