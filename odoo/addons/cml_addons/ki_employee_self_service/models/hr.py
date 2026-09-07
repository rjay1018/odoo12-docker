from odoo import models,api,fields

class Job_Position(models.Model):
    _inherit = 'hr.job'
    
    manpower_request_id = fields.Many2one(
        'manpower.recruit.request',
        string="Manpower Recruitment"
    )
    
    @api.model_cr
    def init(self):
        try:
            rule = self.env.ref('hr_attendance.hr_attendance_rule_attendance_employee')
            rule.perm_read = True
        except:
            pass
        
class Job_Applicant(models.Model):
    _inherit="hr.applicant"
    
    stage_lines_ids = fields.One2many(
        'ki.hr.applicant.stage',
        'request_id',
        readonly=True
    )
    
    @api.multi
    def write(self, vals):
        call_super = super(Job_Applicant,self).write(vals)
        try:
            if vals['stage_id']:
                self.onchange_state_id()
        except:
            pass
        return call_super
    
    def onchange_state_id(self):
        for record in self:
            if record.stage_id:
                if record.stage_lines_ids:
                    (record.stage_lines_ids)[-1].end_time = fields.datetime.now()
                record.stage_lines_ids = [(0,0,{
                    'stage_id' : record.stage_id.id,
                    'start_time' : fields.datetime.now()
                })]

class Job_applicant_stage(models.Model):
    _name = 'ki.hr.applicant.stage'
    _description = 'Hr Applicant Stage'
    
    request_id = fields.Many2one(
        'hr.applicant'
    )
    stage_id = fields.Many2one(
        'hr.recruitment.stage'
    )
    start_time = fields.Datetime(
        required=True,
        string='Start Time',
    )
    end_time = fields.Datetime(
        string='End Time',
    )
    duration = fields.Float(
        string='Duration(Hrs)', 
        compute='_compute_duration_hours', 
        store=True, 
        readonly=True
    )
    duration_days = fields.Float(
        string='Duration(Days)', 
        compute='_compute_duration_hours', 
        store=True, 
        readonly=True
    )
    department_id = fields.Many2one(
        'hr.department',
        related="request_id.department_id",
        string="Deaprtment",
        store=True
    )
    
    @api.depends('start_time', 'end_time')
    def _compute_duration_hours(self):
        for record in self:
            if record.end_time:
                delta = record.end_time - record.start_time
                record.duration = delta.total_seconds() / 3600.0

                if record.duration:
                    record.duration_days = record.duration_days / 24.00

    @api.constrains('start_time', 'end_time')
    def _check_validity_start_and_end(self):
        for record in self:
            if record.start_time and record.end_time:
                if record.end_time < record.start_time:
                    raise exceptions.ValidationError(_('"End Date Time" cannot be earlier than "Start Date Time".'))
