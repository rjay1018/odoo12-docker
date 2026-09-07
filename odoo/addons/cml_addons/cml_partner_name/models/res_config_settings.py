# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    name_formula = fields.Selection(
        [
            ('fml','First MI. Last'),
            ('lfm','Last First MI.'),
            ('flm','First Last Middle')
        ],
        "Name Formula",
#         default='fml',
        config_parameter='cml_partner_name.name_formula'
    )

    def _partner_names_order_selection(self):
        res = super(ResConfigSettings, self)._partner_names_order_selection()
        res  = res + [
            ('fml','First MI. Last'),
            ('lfm','Last First MI.'),
            ('flm','First Last Middle')
        ]
        return res
