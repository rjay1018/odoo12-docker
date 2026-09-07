from odoo import api, fields, models, _


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def onchange_partner_id_custom(self):
        if self.partner_id.global_default_sale_tax_ids:
            self.global_tax_ids = self.partner_id.global_default_sale_tax_ids

