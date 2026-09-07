# -*- coding: utf-8 -*-

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ClientInformation(models.Model):
    _inherit = ['res.partner']

    # def _default_stage_id(self):
    #     team = self._default_team_id(user_id=self.env.uid)
    #     return self._stage_find(team_id=team.id, domain=[('fold', '=', False)]).id

    is_client = fields.Boolean(
        string='Clinic Client',
        store=True,
        default=True
    )
    birthday = fields.Date(
        string='Birthday',
    )
    age = fields.Integer(
        string='Age',
        readonly=False,
        compute='_compute_age',
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
        ('divorced', 'Divorced')],
        string='Civil Status', default='single'
    )
    philhealthid = fields.Char(
        string='PhilHealth',
        help='PhilHealth Number'
    )
    hmo_no = fields.Char(
        string='HMO Account Number',
        help='HMO Account Number'
    )
    hmo_id = fields.Many2one(
        string='HMO Provider',
        comodel_name='hmo.provider',
    )
    appointment_ids = fields.One2many(
        string='Appointment',
        comodel_name='clinic.appointment',
        inverse_name='partner_id',
        domain=[('session_start', '>', fields.Date.today())]
    )

    appt_history_ids = fields.One2many(
        string='Appointment',
        comodel_name='clinic.appointment',
        inverse_name='partner_id',
        domain=[('session_start', '<', fields.Date.today())]
    )

    file_ids = fields.One2many(
        string='Client Files',
        comodel_name='muk_dms.file',
        inverse_name='partner_id',
    )
    case_stage_id = fields.Many2one(
        string='Client Status',
        comodel_name='client.stage',
        track_visibility='always',
        ondelete='restrict',
        tracking=True,
        copy=False
    )

    employee_id = fields.Many2one(
        string='Specialist',
        comodel_name='hr.employee',
        track_visibility="always",
        domain=[('is_specialist', '=', True)]
    )
    specialist_email = fields.Char(
        string='Specialist Email',
        related='employee_id.work_email',
        readonly=True,
        store=True
    )
    specialist_jobtitle = fields.Char(
        string='Job Title',
        related='employee_id.job_title',
        readonly=True,
        store=True
    )
    appointment_type = fields.Selection(
        string='Appointment Type',
        selection=[('inclinic', 'In-Clinic'), ('online', 'Online')]
    )
    clinic_visited = fields.Char(
        string='Clinic Visited',
    )

    hmo_provider = fields.Char(
        string='HMO Provider',
    )

    guardian = fields.Char(
        string='Guardian',
        help='If Minor, Check if Professional if OK with Minor'
    )
    special_priority = fields.Selection(
        string='Special Priority',
        selection=[('pwd', 'PWD'), ('senior', 'Senior Citizen'), ('no', 'No')],
        help='Check with Professional if OK Prioritize',
        default='no'
    )
    emotional = fields.Selection(
        string='Emotional',
        selection=[('vu', 'Very Unhealthy'), ('su', 'Somewhat Unhealthy'),
                   ('sh', 'Somewhat Healthy'), ('vh', 'Very Healthy')],
        help='This is the initial background to be shared with the professional'
    )
    environmental = fields.Selection(
        string='Environmental',
        selection=[('vu', 'Very Unhealthy'), ('su', 'Somewhat Unhealthy'),
                   ('sh', 'Somewhat Healthy'), ('vh', 'Very Healthy')],
        help='This is the initial background to be shared with the professional'
    )
    financial = fields.Selection(
        string='Financial',
        selection=[('vu', 'Very Unhealthy'), ('su', 'Somewhat Unhealthy'),
                   ('sh', 'Somewhat Healthy'), ('vh', 'Very Healthy')],
        help='This is the initial background to be shared with the professional'
    )
    intellectual = fields.Selection(
        string='Intellectual',
        selection=[('vu', 'Very Unhealthy'), ('su', 'Somewhat Unhealthy'),
                   ('sh', 'Somewhat Healthy'), ('vh', 'Very Healthy')],
        help='This is the initial background to be shared with the professional'
    )
    occupational = fields.Selection(
        string='Occupational',
        selection=[('vu', 'Very Unhealthy'), ('su', 'Somewhat Unhealthy'),
                   ('sh', 'Somewhat Healthy'), ('vh', 'Very Healthy')],
        help='This is the initial background to be shared with the professional'
    )
    physical = fields.Selection(
        string='Physical',
        selection=[('vu', 'Very Unhealthy'), ('su', 'Somewhat Unhealthy'),
                   ('sh', 'Somewhat Healthy'), ('vh', 'Very Healthy')],
        help='This is the initial background to be shared with the professional'
    )
    social = fields.Selection(
        string='Social',
        selection=[('vu', 'Very Unhealthy'), ('su', 'Somewhat Unhealthy'),
                   ('sh', 'Somewhat Healthy'), ('vh', 'Very Healthy')],
        help='This is the initial background to be shared with the professional'
    )
    spiritual = fields.Selection(
        string='Spiritual',
        selection=[('vu', 'Very Unhealthy'), ('su', 'Somewhat Unhealthy'),
                   ('sh', 'Somewhat Healthy'), ('vh', 'Very Healthy')],
        help='This is the initial background to be shared with the professional'
    )

    product_id = fields.Many2one(
        string='Service',
        comodel_name='product.product',
        domain=[('type', '=', 'service',)]
    )
    selfharm = fields.Boolean(
        string='Risk of Self Harm?',
        help='If Yes, send SMS to call Helpline as needed'
    )
    selfharm_details = fields.Text(
        string='Specific Details',
        help='If Yes, send SMS to call Helpline as needed'
    )
    taking_meds = fields.Boolean(
        string='Currently Taking Medication?',
        help='If Yes, Refer Straight to Psychiatrist'
    )
    taking_meds_details = fields.Text(
        string='Medication and Doctor Information',
        help='If Yes, Refer Straight to Psychiatrist'
    )
    treatment = fields.Boolean(
        string='Previous / On-going Treatment?',
        help='This is the initial background to be shared with the professional'
    )
    treatment_details = fields.Text(
        string='Specific Details',
        help='This is the initial background to be shared with the professional'
    )
    legalcase = fields.Boolean(
        string='Attending Legal Case?',
        help='Check with Professional if OK'
    )
    legalcase_details = fields.Text(
        string='Additional Details',
        help='Check with Professional if OK'
    )
    problem = fields.Text(
        string='Present Problem',
        help='Use Scoping Matrix for assignment'
    )
    personal_preference = fields.Selection(
        string='Personal Preference',
        selection=[('male', 'Male'),
                   ('female', 'Female'),
                   ('lgbtq', 'LGBTQ+'),
                   ('none', 'No Preference')],
        help='Check pool if available'
    )
    other_info = fields.Text(
        string='Other Information',
        help='Are there any other information you may wish to share that you feel is relevant to consider for our counseling session?'
    )

    client_age = fields.Integer(
        string='Client Age',
    )

    age_group = fields.Selection([
                ('adult', 'Adult'),
                ('minor', 'Minor'),
                ('seniors', 'Seniors'),
                ], string="Age Group", compute='set_age_group', store=True)

    support_ids = fields.Many2many('client.support', 'clinic_support_rel', 'clinic_id', 'support_id',
                                   string="Support Type")

    source_id = fields.Many2one(
        comodel_name='utm.source',
        string="Source",
        copy=False
    )

    emergency_line_ids = fields.One2many(
        string='Emergency Contact',
        comodel_name='emergency.lines',
        inverse_name='partner_id',
    )

    referral_ids = fields.One2many(
        string='Referral Records',
        comodel_name='client.referral',
        inverse_name='partner_id',
    )

    @api.depends('age')
    def set_age_group(self):
        for rec in self:
            if rec.age:
                if rec.age in range(0, 18):
                    rec.age_group = 'minor'
                elif rec.age in range(18, 60):
                    rec.age_group = 'adult'
                else:
                    rec.age_group = 'seniors'

    @api.multi
    @api.depends('birthday')
    def _compute_age(self):
        for record in self:
            age = 0
            if record.birthday:
                age = relativedelta(
                    fields.Date.from_string(fields.Date.today()),
                    fields.Date.from_string(record.birthday)).years
            record.age = age

    @api.multi
    def schedule_appointment(self):
        return {
            'name': _('Appointments'),
            'domain': [('patient_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'clinic.appointment',
            'view_id': False,
            'view_mode': 'form,tree',
            'type': 'ir.actions.act_window',
        }


class HealthProvider(models.Model):
    _name = 'hmo.provider'
    _description = 'HMO Provider'

    name = fields.Char(
        string='Name',
    )


class EmergencyLines(models.Model):
    _name = 'emergency.lines'

    name = fields.Char(
        string='Name',
    )
    contact_number = fields.Char(
        string='Contact Number',
    )
    relationship = fields.Char(
        string='Relationship',
    )

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        ondelete='cascade',
    )

    # specialist_id = fields.Many2one(
    #     string='Specialist',
    #     comodel_name='hr.employee',
    #     track_visibility="always",
    #     domain=[('is_specialist', '=', True)]
    # )

    # support_type = fields.Selection(
    #     string='Type of Support',
    #     selection=[('coach', 'Well-being Coaching'),
    #                ('counseling', 'Counseling'),
    #                ('psychotherpy', 'Psychotherpy'),
    #                ('psychometrician', 'Psychometrician'),
    #                ('psychologist', 'Psychologist'),
    #                ('psychiatrist', 'Psychiatrist'),
    #                ('nutritionist', 'Nutritionist'),]
    # )
