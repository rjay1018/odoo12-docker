# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    
    helpline_ids = fields.One2many(
        string='Helpline Record',
        comodel_name='helpline.sessions',
        inverse_name='partner_id'
    )