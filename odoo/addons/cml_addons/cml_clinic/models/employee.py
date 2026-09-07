# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SpecialistInformation(models.Model):
    _inherit = ['hr.employee']

    @api.multi
    def open_specialist_appointments(self):
        return {
            'name': ('My Appointments'),
            'domain': [('employee_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'clinic.appointment',
            'view_id': False,
            'view_mode': 'tree,calendar,form',
            'type': 'ir.actions.act_window',
        }

    def count_appointment(self):
        count = self.env['clinic.appointment'].search_count([('employee_id', '=', self.id)])
        self.appointment_count = count

   
    appointment_count = fields.Integer(
        string='Appointment Count',
        compute='count_appointment',
    )
    is_specialist = fields.Boolean(
        string="Is Specialist?",
        store=True,
    )
    summary = fields.Html(
        string='Profile Summary'
    )
    specialty_ids = fields.Many2many(
        comodel_name='specialty.tags',
        relation='employee_specialty_rel',
        column1='emp_id',
        column2='specialty_id',
        string='Specialization'
    )

    nonpreference = fields.Many2many(
        comodel_name='specialty.tags',
        relation='employee_nonpreference_rel',
        column1='emp_id',
        column2='nonpref_id',
        string='Non-Preference'
    )
    availability_ids = fields.Many2many(
        comodel_name='specialist.availability',
        relation='specialist_availability_rel',
        column1='emp_id',
        column2='availability_id',
        string='Availability'
    )   
    schedule_line_ids = fields.One2many(
        string='Schedule Line',
        comodel_name='specialist.schedule',
        inverse_name='employee_id',
    )
    extension = fields.Char(
        string='Extension Number',
    )
    
    pseudonym = fields.Char(
        string='Pseudonym',
    )

    _sql_constraints = [
        ('alias_uniq', 'unique (pseudonym)', "Pseudonym name already exists !"),
    ]

    prc_number = fields.Char(
        string='PRC Number',
    )
    ptr_number = fields.Char(
        string='PTR Number',
    )
    s2_license = fields.Char(
        string='S2 License',
    )

    # support_ids = fields.One2many(
    #     comodel_name='support.lines',
    #     inverse_name='employee_id',
    #     string='Support'
    # )


# class SupportType(models.Model):
#     _name = 'support.lines'
    
    # support_id = fields.Many2one(
    #     string='support',
    #     comodel_name='client.support',
    #     ondelete='cascade',
    # )
    # selfrate = fields.Integers(
    #     string='Rate',
    # )
     
    # employee_id = fields.Many2one(
    #     string='Employee',
    #     comodel_name='hr.employee',
    #     ondelete='cascade'
    # )
    # schedule_ids = fields.Many2many('specialist.schedule', 'clinic_schedule_rel', 'schedule_id', 'employee_id',  string="Specialist Schedule")

    