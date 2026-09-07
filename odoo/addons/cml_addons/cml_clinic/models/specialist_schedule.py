from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SpecialistSchedule(models.Model):
    _name = 'specialist.schedule'
    _order = 'day'
    _description = "Specialist Schedule"
    _rec_name = 'employee_id'
    

    name = fields.Char(
        string='Name',
    )
    employee_id = fields.Many2one(
        string='Specialist',
        comodel_name='hr.employee',
        ondelete='cascade'
    )
    
    job_id = fields.Many2one(
        string='Job Position',
        comodel_name='hr.job',
        ondelete='cascade'
    )

    specialty_ids = fields.Many2many(
        string='Specailization',
        comodel_name='specialty.tags',
    )

    timein = fields.Float(
        string='Time Start',
    )
    timeout = fields.Float(
        string='Time End',
    )
    
    appointment_type = fields.Selection(
        string='Appointment Type',
        selection=[
            ('inclinic', 'In-Clinic'),
            ('online', 'Online'),
            ('onsite', 'On-Site'),
            ('offsite', 'Off-Site')]
    )

    day = fields.Selection(
        string='Day',
        selection=[
            ('0', 'Monday'),
            ('1', 'Tuesday'),
            ('2', 'Wednesday'),
            ('3', 'Thursday'),
            ('4', 'Friday'),
            ('5', 'Saturday'),
            ('6','Sunday')],
        default='0',
        required=True
    )

    escalation = fields.Boolean(
        string='Escalation Team',
    )
    
    debrief_ok = fields.Boolean(
        string='Can Debrief',
    )
    
    availability_ids = fields.Many2many('specialist.availability', 'avail_id', 'emp_id', string="Availability")

    # @api.model
    # def default_get(self, fields):
    #     res = super(SpecialistSchedule, self).default_get(fields)
    #     print("test......")
    #     res['employee_id'] = 
    #     return res

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.job_id = self.employee_id.job_id
            self.specialty_ids = self.employee_id.specialty_ids


    @api.constrains('timein','timeout')
    def _slot_validation(self):
        for rec in self:
            if rec.timein < 00.00 or rec.timein > 23.59 :
                raise ValidationError('The Time Start value must be between 0:00 and 23:59!')
        for rec in self:
            if rec.timeout < 00.00 or rec.timeout > 23.59 :
                raise ValidationError('The Time End value must be between 0:00 and 23:59!')

    

    # availability_ids = fields.One2many(
    #     string='Availability',
    #     comodel_name='specialist.availability',
    #     inverse_name='schedule_id',
    # )
    