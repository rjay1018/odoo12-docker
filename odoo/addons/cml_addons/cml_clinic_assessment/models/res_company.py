# -*- coding: utf-8 -*-

from odoo import models, fields


class ResCompany(models.Model):

    _inherit = 'res.company'

    config_consent = fields.Html(
        string='Consent Information',
    )