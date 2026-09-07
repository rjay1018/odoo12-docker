# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    consent = fields.Boolean(
        string='Consent',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help=False
    )

    consent_info = fields.Html(
        string='Consent Information',
        related='company_id.config_consent'
    )
