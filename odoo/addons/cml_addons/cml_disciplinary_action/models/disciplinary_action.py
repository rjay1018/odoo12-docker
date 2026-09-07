from odoo import models, fields, api

class Disciplinary_additional(models.Model):
    _inherit = 'disciplinary.action'
    
    incident_note = fields.Text(
        string='Incident Description',
    )