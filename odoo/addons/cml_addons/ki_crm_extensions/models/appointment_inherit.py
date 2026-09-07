from odoo import models, fields, api


class ClinicAppointmentInherit(models.Model):
    _inherit = 'clinic.appointment'

    crm_id = fields.Many2one(
        'crm.lead',
    )
