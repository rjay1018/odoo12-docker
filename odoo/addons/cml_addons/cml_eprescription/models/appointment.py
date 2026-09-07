from odoo import models, fields, api


class ClinicAppointment(models.Model):
    _inherit = 'clinic.appointment'

    @api.multi
    def open_eprescription(self):
        return {
            'name': ('E-Prescription'),
            'context': {
                        'search_default_partner_id': self.partner_id.id, 
                        'default_partner_id': self.partner_id.id,
                        'default_employee_id': self.employee_id.id,
                        'default_source': self.sequence
                        },
            'view_type': 'form',
            'res_model': 'clinic.eprescription',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }