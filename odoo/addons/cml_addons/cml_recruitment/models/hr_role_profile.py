from odoo import models, fields, api


class HrRoleProfile(models.Model):
    _name = 'hr.role.profile'
    _description = 'Hr Role Profile'
    _order = 'name'

    name = fields.Char(required=True, default=lambda self: ('New'), copy=False)
