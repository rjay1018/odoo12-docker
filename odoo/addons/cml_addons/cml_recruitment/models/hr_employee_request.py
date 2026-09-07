from odoo import fields, models, api, _
from datetime import datetime, date
from odoo.exceptions import ValidationError


class EmployeeRequestType(models.Model):
    _name = 'hr.employee.request.type'

    name = fields.Char(required=True)
    replace = fields.Boolean()


class EmployeeRequest(models.Model):
    _name = 'hr.employee.request'
    _order = 'request_date DESC'
    _description = 'Employee Request'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    STATE = [
        ('draft', 'Draft'),
        ('confirm', 'Confirmed Request'),
        ('approve', 'Approved Request'),
        ('ongoing', 'Recruitment In Progress'),
        ('stop', 'Recruitment Done')
    ]

    @api.multi
    def name_get(self):
        res = []
        for obj in self:
            name = '[%s] %s (%s)' % (obj.name, obj.job_id.name, str(obj.required_employee))
            res += [(obj.id, name)]
        return res

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('hr.emp.req.ref.no') or '/'
        return super(EmployeeRequest, self).create(vals)

    @api.multi
    def unlink(self):
        for obj in self:
            if obj.state != 'draft':
                raise ValidationError('You cannot delete a request which is not in draft state')
        return super(EmployeeRequest, self).unlink()

    @api.multi
    def _get_default_request_type(self):
        req_type = self.env.ref('cml_recruitment.emp_req_type_new', None)
        return req_type.id if req_type else None

    name = fields.Char('Reference #')
    job_id = fields.Many2one('hr.job', 'Job Position', required=True)
    job_desc = fields.Text(related='job_id.description', string='Job Description', store=True)
    job_address_id = fields.Many2one(related='job_id.address_id', model='res.partner', string='Job Location', store=True)
    job_address_group_id = fields.Many2one(related='job_id.address_group_id', model='hr.address.group', string='Location Group', store=True)
    job_level_id = fields.Many2one(related='job_id.job_level_id', model='hr.job.level', string='Job Level', store=True)
    job_category_id = fields.Many2one(related='job_id.job_category_id', model='hr.job.category', string='Job Category', store=True)
    required_employee = fields.Integer('Required Employee',  default=1, required=True, help='Number of required employee for this job position')
    state = fields.Selection(STATE, default='draft')
    request_date = fields.Datetime('Date of Request', required=True, default=lambda *d: datetime.now())
    request_approve = fields.Date('Request Approved')
    recruit_start = fields.Date('Recruitment Start')
    recruit_stop = fields.Date('Recruitment Stop')
    applicant_ids = fields.One2many('hr.applicant', 'emp_request_id', 'Applicants')
    color = fields.Integer()
    application_count = fields.Integer(compute='_count_applicants', store=True)
    request_duration = fields.Integer('Duration (Days)', compute='_compute_duration', store=True)
    request_type_id = fields.Many2one('hr.employee.request.type', required=True, default=_get_default_request_type)
    request_type_replace = fields.Boolean(related='request_type_id.replace', store=True)
    replacement_for_ids = fields.Many2many(comodel_name='hr.employee', string='Replacement For')
    requested_by = fields.Many2one('hr.employee')

    @api.multi
    @api.depends('recruit_stop', 'request_approve')
    def _compute_duration(self):
        for obj in self:
            duration = 0
            if obj.request_approve and obj.recruit_stop:
                delta = obj.recruit_stop - obj.request_approve
                duration = delta.days
            obj.request_duration = duration

    @api.multi
    @api.depends('applicant_ids')
    def _count_applicants(self):
        for obj in self:
            obj.application_count = len(obj.applicant_ids)

            if obj.application_count > obj.required_employee:
                raise ValidationError(_('Employee Request: %s has reached its maximum required employee/applicant.\n\n \
                    Required Employee: %s' % (obj.name, obj.required_employee)))

    def _get_state(self, key):
        return [v for k, v in self.STATE if k == key][0]

    def action_draft(self):
        self.recruit_start = None
        self.recruit_stop = None
        self.state = 'draft'

    def action_confirm(self):
        self._message_post(
            body='Status Changed: %s to Confirmed Request' % (self._get_state(self.state))
        )
        self.state = 'confirm'

    def action_approve(self):
        self._message_post(
            body='Status Changed: %s to Approved Request' % (self._get_state(self.state))
        )
        self.request_approve = date.today()
        self.state = 'approve'

    def action_start(self):
        self._message_post(
            body='Status Changed: %s to Recruitment Ongoing' % (self._get_state(self.state))
        )
        self.recruit_start = date.today()
        self.state = 'ongoing'

    def action_stop(self):
        self._message_post(
            body='Status Changed: %s to Recruitment Stop' % (self._get_state(self.state))
        )
        self.recruit_stop = date.today()
        self.state = 'stop'

    def _message_post(self, subject=None, body=''):
        self.message_post(
            subject=subject,
            body=_(body)
        )


class Job(models.Model):
    _inherit = 'hr.job'

    emp_request_ids = fields.One2many('hr.employee.request', 'job_id')


class Applicant(models.Model):
    _inherit = 'hr.applicant'

    @api.multi
    def name_get(self):
        res = []
        for obj in self:
            name = obj.name
            if obj.partner_name:
                name = '%s - %s' %(name, obj.partner_name)
            if obj.stage_id:
                name = '%s (%s)' %(name, obj.stage_id.name)
            res += [(obj.id, name)]
        return res

    emp_request_id = fields.Many2one('hr.employee.request', 'Employee Request')
    job_offer_date = fields.Date()

    @api.onchange('emp_request_id')
    def onchange_emp_request(self):
        self.job_id = self.emp_request_id.job_id.id        
        self.department_id = self.emp_request_id.job_id.department_id.id
        self.address_id = self.emp_request_id.job_address_id.id
