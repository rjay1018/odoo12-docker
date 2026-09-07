from odoo import fields, models, api


class ResParnterYYY(models.Model):  
    _inherit = 'res.partner'

    contact_person_name = fields.Char(string='Contact Person')
    contact_person_number = fields.Char(string='Contact Number')
    