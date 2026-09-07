# -*- coding: utf-8 -*-
from odoo import fields, models


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    consumption = fields.Selection([
        ('strict', 'Strict'),
        ('flexible', 'Flexible')],
        help="Defines if you can consume more or less components than the quantity defined on the BoM.",
        default='strict',
        string='Consumption'
    )
