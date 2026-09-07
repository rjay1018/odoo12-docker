# -*- coding: utf-8 -*-

from odoo import models, fields, api,  _



class ClientFile(models.Model):
    _inherit = 'muk_dms.file'

    partner_id = fields.Many2one(
        string='Client Name',
        comodel_name='res.partner',
        ondelete='restrict',
    )