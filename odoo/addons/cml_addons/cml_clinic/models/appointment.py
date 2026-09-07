# -*- coding: utf-8 -*-

from odoo import models, fields, api

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError


class ClinicAppointments(models.Model):
    _name = 'clinic.appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Appointment Schedule'
    _order = 'session_start,sequence'
    _rec_name = 'sequence'

    @api.model
    def create(self, vals):
        if vals.get('sequence', ('New')) == ('New'):
            vals['sequence'] = self.env['ir.sequence'].next_by_code('clinic.appointment.sequence') or ('New')
        result = super(ClinicAppointments, self).create(vals)
        return result

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_validated(self):
        self.write({'state': 'validated'})

    @api.multi
    def action_send_appointment(self):
        # template_id = self.env.ref('cml_clinic.clinic_email_invite').id
        # template = self.env['mail.template'].browse(template_id)
        # template.send_mail(self.id, force_send=True)

        self.ensure_one()
        template_id = self.env['ir.model.data'].xmlid_to_res_id('cml_clinic.clinic_email_invite',
                                                                raise_if_not_found=False)
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        if template.lang:
            lang = template._render_template(template.lang, 'clinic.appointment', self.id)
        ctx = {
            'default_model': 'clinic.appointment',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            # 'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'model_description': self.with_context(lang=lang),
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    name = fields.Char(
        string='Name',
    )
    sequence = fields.Char(
        string='Appointment Number',
        required=True, copy=False, readonly=True,
        index=True, default=lambda self: ('New')
    )
    product_id = fields.Many2one(
        string='Service',
        comodel_name='product.product',
        readonly=True,
        states={'draft': [('readonly', False)]},
        domain=[('type', '=', 'service',)]
    )
    employee_id = fields.Many2one(
        string='Specialist',
        comodel_name='hr.employee',
        readonly=True,
        track_visibility="always",
        states={'draft': [('readonly', False)]},
        required=True
    )
    supervisor_notes = fields.Text(
        string='Supervisor Notes',
        readonly=True,
        states={'done': [('readonly', False)]},
    )
    partner_id = fields.Many2one(
        string='Client',
        comodel_name='res.partner',
        readonly=True,
        states={'draft': [('readonly', False)]},
        domain=[('customer', '=', 'True',)]
    )
    state = fields.Selection(
        string='Status',
        selection=[('draft', 'Draft'),
                   ('confirmed', 'Confirmed'),
                   ('done', 'Done'),
                   ('validated', 'Validated'),
                   ('cancel', 'Cancelled')],
        default='draft',
        track_visibility="always",
        readonly=True,
    )
    duration = fields.Float(
        string='Duration',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    session_start = fields.Datetime(
        string='Start',
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=fields.Datetime.now,
    )
    session_end = fields.Datetime(
        string='End',
        compute='_get_end_time',
        store=True
    )
    context = fields.Text(
        string='Context',
        readonly=True,
        states={'draft': [('readonly', False)], 'confirmed': [('readonly', False)]},
    )
    presenting_problem = fields.Text(
        string='Presenting Problem',
        readonly=True,
        states={'draft': [('readonly', False)], 'confirmed': [('readonly', False)]},
    )
    assessment = fields.Text(
        string='Assessment',
        readonly=True,
        states={'draft': [('readonly', False)], 'confirmed': [('readonly', False)]},
    )
    interventions = fields.Text(
        string='Interventions',
        readonly=True,
        states={'draft': [('readonly', False)], 'confirmed': [('readonly', False)]},
    )
    agreed_astep = fields.Text(
        string='Agreed Action Step',
        readonly=True,
        states={'draft': [('readonly', False)], 'confirmed': [('readonly', False)]},
    )
    notes = fields.Text(
        string='Specialist Notes',
        readonly=True,
        states={'draft': [('readonly', False)], 'confirmed': [('readonly', False)]},
    )
    appointment_type = fields.Selection(
        string='Appointment Type',
        readonly=True,
        states={'draft': [('readonly', False)]},
        selection=[('inclinic', 'In-Clinic'), ('online', 'Online')]
    )
    apt_start = fields.Datetime(
        string='Session Start',
        default=fields.Datetime.now,
        readonly=True,
        states={'confirmed': [('readonly', False)]},
    )

    apt_stop = fields.Datetime(
        string='Session Stop',
        default=fields.Datetime.now,
        readonly=True,
        states={'confirmed': [('readonly', False)]},
    )
    user_id = fields.Many2one('res.users', string="Contact Person", default=lambda self: self.env.uid)

    for_refferal = fields.Boolean(
        string='For Referral',
    )

    meeting_link = fields.Char(
        string='Meeting Link',
    )

    website_id = fields.Many2one(
        string='Website Registered',
        related='partner_id.website_id',
        readonly=True
    )

    is_member = fields.Boolean(
        string='Is a Member',
        store=True,
        compute='_compute_member'
    )

    @api.depends('partner_id')
    def _compute_member(self):
        for i in self:
            if i.partner_id.membership_state in ['free', 'paid']:
                i.is_member = True
            else:
                i.is_member = False

    @api.multi
    @api.depends('session_start', 'duration')
    def _get_end_time(self):
        for rec in self:
            if not (rec.session_start and rec.duration):
                rec.session_end = rec.session_start
                continue
            time_duration = timedelta(hours=rec.duration)
            rec.session_end = rec.session_start + time_duration
            pass

    @api.constrains('duration')
    def _duration_validation(self):
        for rec in self:
            if rec.duration < 00.00 or rec.duration > 23.59:
                raise ValidationError(('The Duration value must be between 0:00 and 23:59!'))

    # timeslot_id = fields.Many2one(
    #     string='Time Schedule',
    #     comodel_name='clinic.timeslot',
    #     required=True,
    # )
    # patient_id = fields.Many2one(
    #     string='Patient',
    #     comodel_name='clinic.patient',
    # )
    # contact_number = fields.Char(
    #     string='Contact Number',
    # )
    # email_address = fields.Char(
    #     string='Email Address',
    # )
    # age = fields.Integer(
    #     string='Age',
    #     related='partner_id.age'
    # )
    # appointment_date= fields.Date(
    #     string='Date Time'
    # )
    # diff = fields.Datetime.from_string(rec.apt_stop) - fields.Datetime.from_string(rec.apt_start)
    # mins = round(diff.total_seconds()/ 60.0, 2)
    # rec.apt_duration = '{:02d}:{:02d}'.format(*divmod(mins, 60))

    # apt_duration = fields.Float(
    #     string='Session Duration',
    #     compute='_compute_apt_timer',
    #     store=True
    # )

    # @api.multi
    # @api.depends('apt_start','apt_stop','apt_duration')
    # def _compute_apt_timer(self):
    #     for rec in self:
    #         diff = fields.Datetime.from_string(rec.apt_stop) - fields.Datetime.from_string(rec.apt_start)
    #         n = round(diff.total_seconds())
    #         result = timedelta(seconds = n)
    #         rec.apt_duration = float(result or 0.00)
