# -*- coding: utf-8 -*-

from odoo import models, fields, api,  _


class CreateAppointment(models.TransientModel):
    _name = 'create.appointment'
    _description = 'Create Appointment'
    
    partner_id = fields.Many2one(
        string='Client Name',
        comodel_name='res.partner',
    )
    product_id = fields.Many2one(
        string='Service',
        comodel_name='product.product',
        domain=[('type','=','service',)]
    )
    appointment_type = fields.Selection(
        string='Appointment Type',
        selection=[('inclinic', 'In-Clinic'), ('online', 'Online')]
    )
    session_start = fields.Datetime(
        string='Schedule',
    )
    duration = fields.Float(
        string='Duration',
    )
    employee_id = fields.Many2one(
        string='Specialist',
        comodel_name='hr.employee',
    )
    # timeslot_id = fields.Many2one(
    #     string='Time Schedule',
    #     comodel_name='clinic.timeslot',
    # )
    # appointment_date = fields.Date(
    #     string='Appointment Date',
    #     default=fields.Date.context_today,
    # )    


    # @api.multi
    # @api.depends('session_end','duration')
    # def _get_end_time(self):
    #     for rec in self:
    #         if not (rec.session_start and rec.duration):
    #             rec.session_end = rec.session_start
    #             continue
    #         time_duration = timedelta(hours=rec.duration)
    #         rec.session_end = rec.session_start + time_duration
    #         pass

    # def _set_end_date(self):
    #     pass

    @api.constrains('duration')
    def _duration_validation(self):
        for rec in self:
            if rec.duration < 00.00 or rec.duration > 23.59 :
                raise ValidationError(('The Duration value must be between 0:00 and 23:59!'))
        
    def action_create(self):
        vals = {
             'partner_id'   : self.partner_id.id,
             'duration'     :   self.duration,
             'session_start'  : self.session_start,
             'employee_id'  : self.employee_id.id,
             'product_id'   : self.product_id.id,
             'appointment_type' : self.appointment_type

        }
        self.env['clinic.appointment'].create(vals)