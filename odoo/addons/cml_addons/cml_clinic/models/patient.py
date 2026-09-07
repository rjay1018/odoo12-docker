# -*- coding: utf-8 -*-

from odoo import models, fields, api,  _
from odoo.exceptions import ValidationError

class PatientInformation(models.Model):
    _name = 'clinic.patient'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = 'Patient Information'
    
    image = fields.Binary(
        string='Photo',
    )
    name = fields.Char(
        string='Name', 
        required=True
    )
    contact = fields.Char(
        string='Contact Number',
    )
    companyinfo = fields.Char(
        string='Company',
    )
    business_address = fields.Char(
        string='Business Address',
    )
    account_number = fields.Char(
        string='Account Number',
    )
    birthday = fields.Date(
        string='Birthday',
    )
    age = fields.Integer(
        string='Age',
    )
    sex = fields.Selection([
            ('male', 'Male'),
            ('female', 'Female')
            ], string='Sex'
    )
    marital = fields.Selection([
            ('single', 'Single'),
            ('married', 'Married'),
            ('separated', 'Separated'),
            ('widowed', 'Widowed'),
            ('divorced', 'Divorced')
            ], string='Civil Status', default='single'
    )
    notes = fields.Text(
        string='Other Information',
    )
    patient_seq = fields.Char(
        string='Patient Number', 
        required=True, copy=False, readonly=True, 
        index=True, default=lambda self: _('New')
    )
    appointment_count = fields.Integer(
        string='Appointment Count',
        compute='count_appointment',
    )
    
    @api.model
    def create(self, vals):
        if vals.get('patient_seq', _('New')) == _('New'):
            vals['patient_seq'] = self.env['ir.sequence'].next_by_code('clinic.patient.sequence') or _('New')
        result = super(PatientInformation, self).create(vals)
        return result

    # @api.multi
    # def open_patient_appointments(self):
    #     return {
    #         'name': _('Appointments'),
    #         'domain': [('patient_id', '=', self.id)],
    #         'view_type': 'form',
    #         'res_model': 'clinic.appointment',
    #         'view_id': False,
    #         'view_mode': 'tree,form',
    #         'type': 'ir.actions.act_window',
    #     }

    # def count_appointment(self):
    #     count = self.env['clinic.appointment'].search_count([('patient_id', '=', self.id)])
    #     self.appointment_count = count