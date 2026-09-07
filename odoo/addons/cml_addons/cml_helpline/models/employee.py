# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    
    helpline_agent = fields.Boolean(
        string='Helpline Agent',
    )