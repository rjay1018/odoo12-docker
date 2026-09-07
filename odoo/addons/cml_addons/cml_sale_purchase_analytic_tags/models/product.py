# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductTemplate(models.Model):

    _inherit = "product.template"
    
    purchase_analytic_tag_ids = fields.Many2many(
        'account.analytic.tag',
        string='Purchase Analytic Tags',
    )
    sale_analytic_tag_ids = fields.Many2many(
        'account.analytic.tag',
        string='Sale Analytic Tags',
    )
    