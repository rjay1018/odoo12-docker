from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'


    @api.multi
    def action_confirm(self):
        for record in self:
            company_missing_line = record.order_line.filtered(lambda i: not i.company_id)
            if company_missing_line:
                company_missing_line.update({
                    'company_id': record.company_id.id
                })
        return super(SaleOrder, self).action_confirm()