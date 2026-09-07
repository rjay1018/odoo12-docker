from odoo import models, fields, api, tools, _
from datetime import datetime
from dateutil import parser as dateutil_parser
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class PassSlip(models.Model):
    _name = 'hr.pass.slip'
    _rec_name = 'employee_id'
    _order = 'time_out desc'

    STATE = [
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('approve', 'Approve')
    ]

    TRANSACT = [
        ('o', 'Official'),
        ('p', 'Personal'),
    ]

    @api.depends('time_out', 'time_in', 'contract_id')
    def _compute_duration(self):
        self.duration = 0
        obj_att = self.env['hr.attendance']

        if self.time_out and self.time_in:
            time_out = obj_att._localize_dt(self.time_out)
            time_out = fields.Datetime.to_string(time_out)
            new_time_out = dateutil_parser.parse(time_out)
            new_time_out = new_time_out.replace(second=0)

            time_in = obj_att._localize_dt(self.time_in)
            time_in = fields.Datetime.to_string(time_in)
            new_time_in = dateutil_parser.parse(time_in)
            new_time_in = new_time_in.replace(second=0)

            diff_in = new_time_in - new_time_out
            duration = diff_in.total_seconds() / 3600.0
            if duration > 0:
                self.duration = duration

            self.date = fields.Date.to_date(time_out)

            pp = self.env['hr.payroll.period']._get_payroll_period(self.payroll_schedule, self.date)
            self.payroll_period_id = pp.id if pp else None

    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    contract_id = fields.Many2one('hr.contract', 'Contract', required=True)
    payroll_schedule = fields.Selection(related='contract_id.payroll_schedule', store=True)
    time_out = fields.Datetime('Time Out', default=lambda *d: datetime.now())
    time_in = fields.Datetime('Time In', default=lambda *d: datetime.now() + relativedelta(hours=1))
    duration = fields.Float(compute=_compute_duration, store=True)
    date = fields.Date(string='Attendance Date', compute=_compute_duration, store=True, required=True)
    destination = fields.Char()
    notes = fields.Text(string='Remarks')
    state = fields.Selection(STATE, default='draft')
    payroll_period_id = fields.Many2one('hr.payroll.period', compute=_compute_duration, string='Payroll Period', store=True)
    transaction_type = fields.Selection(TRANSACT, default='o', required=True)

    @api.onchange('employee_id')
    def onchange_employee(self):
        self.contract_id = None
        if self.employee_id:
            self.contract_id = self.env['hr.contract'].get_active_contract(self.employee_id)

    @api.multi
    def action_confirm(self):
        if self.duration <= 0:
            raise ValidationError(_('Duration must be greater to zero'))
        self.state = 'confirm'

    @api.multi
    def action_approve(self):
        if self.duration <= 0:
            raise ValidationError(_('Duration must be greater to zero'))
        self.state = 'approve'

    @api.multi
    def action_draft(self):
        self.state = 'draft'
