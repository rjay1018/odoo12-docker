from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    global_default_sale_tax_ids = fields.Many2many(
        'account.tax',
        string='Global Default Sale Tax',
    )

    global_default_purchase_tax_ids = fields.Many2many(
        'account.tax',
        string='Global Default Purchase Tax',
    )
