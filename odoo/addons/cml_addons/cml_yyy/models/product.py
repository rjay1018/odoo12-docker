from odoo import fields, models, api


class ProductTemplateYYY(models.Model):
    _inherit = 'product.template'

    default_code = fields.Char(
        'Product Code', compute='_compute_default_code',
        inverse='_set_default_code', store=True)

    description_qa = fields.Html('Description for QA')

class ProductProductYYY(models.Model):
    _inherit = 'product.product'

    default_code = fields.Char('Product Code', index=True)

