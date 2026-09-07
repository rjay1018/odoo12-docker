from odoo import models, fields, api


class Job(models.Model):
    _inherit = 'hr.job'

    JOB_OVERSEES = [
        ('wide', 'Enterprise Wide'),
        ('dept', 'Department'),
        ('section', 'Section'),
        ('team', 'Team'),
        ('unit', 'Unit')
    ]

    EDU_LEVEL = [
        ('high', 'Highschool'),
        ('vocational', '2years / Vocational'),
        ('college', 'College Graduate'),
        ('post', 'Post Graduate')
    ]
    
    approved_headcount = fields.Integer()
    job_level_id = fields.Many2one('hr.job.level', 'Job Level', ondelete='restrict')
    job_category_id = fields.Many2one('hr.job.category', 'Job Category', ondelete='restrict')    
    address_group_id = fields.Many2one('hr.address.group', 'Location Group', ondelete='restrict')
    state = fields.Selection(selection_add=[('cancel', 'Canceled'),('hold', 'Hold')])
    opening_date = fields.Date(default=fields.Date.context_today)
    requestor = fields.Char('Requested By')

    competency_ids = fields.Many2many(
        string='Competency',
        comodel_name='hr.competency',
        relation='hr_competency_job_rel',
        column1='hr_competency_id',
        column2='job_id'
    )

    job_function_ids = fields.One2many('hr.job.funtions', 'jobs_id', string='Job Functions')

    contract_ids = fields.One2many('hr.contract', 'job_id',
        string='Related Contract',
        domain=["|", ("state", "=", "close"), ("state", "=", "cancel")]
    )

    succession_ids = fields.One2many('succession.plan', 'jobs_id', string='Succession Plan')
    job_oversees = fields.Selection(JOB_OVERSEES, 'Oversees')
    reporting_to = fields.Char()
    career_prog = fields.Char('Career Progression')

    # Pre-qualifications
    ed_level = fields.Selection(EDU_LEVEL, 'Education Level')
    course = fields.Char()
    cert_req = fields.Char('Certification / License')
    special_training = fields.Char('Specialized Training')
    yr_exp = fields.Integer('Years of Experience')
    shift_sched = fields.Boolean('Shifting Schedule')
    travel = fields.Boolean('Travel (Intl / Local)')

    # HR Reference
    effective_date = fields.Date('Effectivity Date')
    revision_no = fields.Integer('Revision No.')
    reference_no = fields.Integer('Reference No.')

    def set_cancel(self):
        self.state = 'cancel'

    def set_hold(self):
        self.state = 'hold'


class HrJobLevel(models.Model):
    _name = 'hr.job.level'

    name = fields.Char(required=True)
    description = fields.Text()
    active = fields.Boolean(default=True)


class HrJobCategory(models.Model):
    _name = 'hr.job.category'

    name = fields.Char(required=True)
    description = fields.Text()
    active = fields.Boolean(default=True)


class HrAddressGroup(models.Model):
    _name = 'hr.address.group'

    name = fields.Char(required=True)
    description = fields.Text()
    active = fields.Boolean(default=True)
