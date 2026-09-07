from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil import parser as dateutil_parser


class Undertime(models.Model):
    _name = 'hr.undertime'

    STATE = [
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('for_approval', 'Recommending Approval'),
        ('approve', 'Approved'),
        ('cancel', 'Cancelled')
    ]

    @api.multi
    def name_get(self):
        obj_att = self.env['hr.attendance']
        res = super(Undertime, self).name_get()
        for obj in self:
            name = '%s [ %s ]' % (obj.employee_id.name, obj_att._format_sched_time(obj.ut_hours))
            res.append((obj.id, name))
        return res

    @api.depends('ut_fr', 'ut_to')
    def _compute_ut(self):
        obj_att = self.env['hr.attendance']
        if self.ut_fr and self.ut_to:
            ut_fr = obj_att._localize_dt(self.ut_fr)
            ut_fr = fields.Datetime.to_string(ut_fr)
            new_ut_fr = dateutil_parser.parse(ut_fr)
            new_ut_fr = new_ut_fr.replace(second=0)

            ut_to = obj_att._localize_dt(self.ut_to)
            ut_to = fields.Datetime.to_string(ut_to)
            new_ut_to = dateutil_parser.parse(ut_to)
            new_ut_to = new_ut_to.replace(second=0)

            diff = new_ut_to - new_ut_fr
            self.ut_hours = diff.total_seconds() / 3600.0

    @api.onchange('employee_id', 'ut_fr')
    def onchange_employee(self):
        if self.employee_id:
            self.contract_id = self.env['hr.contract'].get_active_contract(self.employee_id)
            if self.contract_id:
                pp = self.env['hr.payroll.period']._get_payroll_period(self.contract_id.payroll_schedule, self.ut_fr)
                self.payroll_period_id = pp.id if pp else None

    employee_id = fields.Many2one('hr.employee', required=True)
    contract_id = fields.Many2one('hr.contract')
    state = fields.Selection(STATE, default='draft')
    ut_fr = fields.Datetime('From', required=True)
    ut_to = fields.Datetime('To', required=True)
    ut_hours = fields.Float(compute=_compute_ut, string='Duration (HH:MM)', store=True)
    payroll_period_id = fields.Many2one('hr.payroll.period')
    notes = fields.Text(required=True)

    def state_draft(self):
        self.state = 'draft'

    def state_confirm(self):
        self.state = 'confirm'

    def state_for_approval(self):
        self.state = 'for_approval'

    def state_approve(self):
        self.state = 'approve'

    def state_cancel(self):
        self.state = 'cancel'