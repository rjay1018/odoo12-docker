from odoo import models, fields, api, _
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from datetime import date, datetime, timedelta
from pytz import timezone, UTC
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


ALLOC_STATE = [
    ('draft', 'Draft'),
    ('confirm', 'Confirmed'),
    ('validate', 'Approved'),
    ('expire', 'Expired'),
    ('refuse', 'Cancelled')
]

class LeaveType(models.Model):
    _inherit = 'hr.leave.type'

    TYPE = [
        ('paid', 'Paid Leave'),
        ('unpaid', 'Unpaid Leave'),
        ('halfpaid', 'Half Paid Leave')
    ]

    leave_type = fields.Selection(TYPE, string='Type', required=True, default='paid')
    timesheet_generate = fields.Boolean('Generate Timesheet', default=False)
    notes = fields.Text()
    absence = fields.Boolean(string='Leave of Absence', default=False)

    @api.multi
    def name_get(self):
        res = super(LeaveType, self).name_get()
        for obj in self:
            res.append((obj.id, obj.name))
        return res


class LeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'
    _order = 'valid_to desc, employee_id'

    @api.multi
    def name_get(self):
        res = []
        for obj in self:
            if obj.employee_id:
                name = "%s (%.2f days of %s | %s)" % (obj.employee_id.name, obj.total_allocation, obj.holiday_status_id.name, obj.fiscal_year_id.name)
            else:
                name = obj.holiday_status_id.name
            res.append((obj.id, name))
        return res

    @api.multi
    @api.depends('leave_ids.state', 'total_allocation')
    def _compute_leaves(self):
        for obj in self:
            leave_cnt = leave_bal = 0
            for l in obj.leave_ids:
                if l.state == 'approve':
                    leave_cnt += l.number_of_days
            obj.leave_count = leave_cnt
            obj.leave_balance = obj.total_allocation - leave_cnt

    @api.model
    def _default_employee(self):
        emp = None
        if self.env.uid > 2:
            emp = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return emp

    @api.multi
    @api.depends('accumulated_leave', 'number_of_days')
    def _compute_allocation(self):
        for obj in self:
            obj.total_allocation = obj.accumulated_leave + obj.number_of_days

    employee_id = fields.Many2one('hr.employee', string='Employee', index=True, readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, default=_default_employee)
    holiday_status_id = fields.Many2one('hr.leave.type', string='Leave Type', required=False, readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, default=None)
    number_of_days = fields.Float(string='Number of Days', required=True, default=5)
    accumulated_leave = fields.Float(default=0)
    total_allocation = fields.Float(compute=_compute_allocation, store=True)
    convertible_leave = fields.Float(required=True, default=0)
    leave_count = fields.Float(compute=_compute_leaves, string='Leaves Taken', store=True)
    leave_balance = fields.Float(compute=_compute_leaves, string='Remaining Leaves', store=True)
    state = fields.Selection(ALLOC_STATE, default='draft')
    fiscal_year_id = fields.Many2one('account.fiscal.year', string='Fiscal Year')
    leave_ids = fields.One2many('hr.leave', 'leave_allocation_id', required=False)
    absence = fields.Boolean(string='Leave of Absence', default=False)
    valid_from = fields.Date(required=False)
    valid_to = fields.Date(required=False)
    converted = fields.Boolean()
    payslip_id = fields.Many2one('hr.payslip', 'Ref. Payslip')

    _sql_constraints = [
        ('employee_leave_type_check', 'UNIQUE(employee_id, holiday_status_id, fiscal_year_id)', 'Leave allocation already exists for this employee on this fiscal year')
    ]

    @api.multi
    @api.constrains('holiday_status_id')
    def _check_leave_type_validity(self):
        pass

    @api.multi
    def unlink(self):
        for obj in self:
            if obj.state != 'draft':
                raise ValidationError(_('You cannot delete a leave allocation which is not in Draft state'))
        return super(LeaveAllocation, self).unlink()

    @api.onchange('fiscal_year_id', 'holiday_status_id')
    def onchange_fiscal_year(self):
        self.valid_from = None
        self.valid_to = None
        if self.fiscal_year_id:
            self.valid_from = self.fiscal_year_id.date_from
            self.valid_to = self.fiscal_year_id.date_to
            self.accumulated_leave = self._get_unused_leaves()

    def _get_unused_leaves(self):
        unused_leaves = 0
        accu_annual_leave = bool(self.env['ir.config_parameter'].sudo().get_param('leaves.accumulated_annual_leave'))
        if accu_annual_leave:
            if self.fiscal_year_id and self.holiday_status_id:
                prev_fy = self.env['account.fiscal.year']._previous_year(self.fiscal_year_id.id)
                args = [
                    ('employee_id', '=', self.employee_id.id),
                    ('holiday_status_id', '=', self.holiday_status_id.id),
                    ('fiscal_year_id', '=', prev_fy.id),
                    ('converted', '=', False)
                ]
                res = self.search(args)
                unused_leaves = res.leave_balance
        return unused_leaves

    @api.multi
    def action_draft(self):
        self.state = 'draft'

    @api.multi
    def action_confirm(self):
        self.state = 'confirm'

    @api.multi
    def action_approve(self):
        self.state = 'validate'

    @api.multi
    def action_expire(self):
        if self.id == self._get_loa_id():
            raise ValidationError(_('Action is not possible for pre-code allocation'))

        self.state = 'expire'

    @api.multi
    def action_refuse(self):
        if self.id == self._get_loa_id():
            raise ValidationError(_('Action is not possible for pre-code allocation'))

        self.state = 'refuse'

    def _get_loa_id(self):
        return self.env.ref('ph_payroll_leave.leave_alloc_absence', None).id

    @api.multi
    def _cron_check_validity(self):
        today = date.today()
        args = [
            ('valid_to', '<', today),
            ('state', '=', 'validate'),
            ('employee_id', '!=', False),
            ('absence', '=', False)
        ]
        allocations = self.search(args)
        for alloc in allocations:
            alloc.state = 'expire'


class LeaveRequest(models.Model):
    _inherit = 'hr.leave'

    STATE = [
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('for_approval', 'Recommending Approval'),
        ('approve', 'Approved'),
        ('cancel', 'Cancelled')
    ]

    @api.multi
    def unlink(self):
        for obj in self:
            if obj.state != 'draft':
                raise ValidationError(_("You cannot delete a leave request which is not in 'Draft' state"))
        return super(LeaveRequest, self).unlink()

    @api.model
    def _default_employee(self):
        emp = None
        if self.env.uid > 2:
            emp = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return emp

    employee_id = fields.Many2one('hr.employee', string='Employee', index=True, readonly=False,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, default=_default_employee)
    contract_id = fields.Many2one('hr.contract', 'Contract', required=True)
    leave_allocation_id = fields.Many2one('hr.leave.allocation', string='Leave Allocation', required=False, ondelete='cascade')
    holiday_status_id = fields.Many2one(related='leave_allocation_id.holiday_status_id', model='hr.leave.type', string='Leave Type', store=True, required=False)
    leave_date_ids = fields.One2many('hr.leave.date', 'leave_id', string='Leave Dates')
    leave_balance = fields.Float(string='Remaining Leaves', default=0)
    absence = fields.Boolean(string='Leave of Absence', default=False)
    state = fields.Selection(STATE, readonly=True, track_visibility='onchange', copy=False, default='draft')

    @api.onchange('employee_id')
    def onchange_employee(self):
        self.contract_id = None
        if self.employee_id:
            self.contract_id = self.env['hr.contract'].get_active_contract(self.employee_id)

    @api.onchange('holiday_type')
    def _onchange_type(self):
        pass

    @api.onchange('request_date_from', 'request_date_to')
    def _onchange_request_parameters(self):
        hour_from = float_to_time(8)
        hour_to = float_to_time(17)

        tz = self.env.user.tz if self.env.user.tz and not self.request_unit_custom else 'Asia/Manila'  # custom -> already in UTC
        self.date_from = timezone(tz).localize(datetime.combine(self.request_date_from, hour_from)).astimezone(UTC).replace(tzinfo=None)
        self.date_to = timezone(tz).localize(datetime.combine(self.request_date_to, hour_to)).astimezone(UTC).replace(tzinfo=None)

    @api.onchange('absence')
    def onchange_absence(self):
        self.leave_allocation_id = None
        if self.absence:
            self.leave_allocation_id = self.leave_allocation_id._get_loa_id()

    @api.onchange('leave_allocation_id')
    def onchange_leave_allocation(self):
        self.leave_balance = self.leave_allocation_id.leave_balance

    @api.constrains('state', 'number_of_days', 'holiday_status_id')
    def _check_holidays(self):
        pass

    @api.multi
    @api.constrains('holiday_status_id', 'date_to', 'date_from')
    def _check_leave_type_validity(self):
        pass

    def _parse_dates(self, fr, to):
        date_list = []
        for n in range(int((to - fr).days)+1):
            date_list.append(fr + timedelta(n))
        return date_list

    def _compute_dates(self, fr, to):
        self.leave_date_ids = None
        for d in self._parse_dates(fr, to):
            pay_period = self.env['hr.payroll.period']._get_payroll_period(self.contract_id.payroll_schedule, d)
            vals = {
                'date': d,
                'leave_id': self.id,
                'payroll_period_id': pay_period.id if pay_period else None,
            }
            self.leave_date_ids = [(0, 0, vals)]

    @api.onchange('request_date_from', 'request_date_to', 'request_unit_half', 'contract_id')
    def _onchange_leave_dates(self):
        fr = fields.Date.to_date(self.request_date_from)
        to = fields.Date.to_date(self.request_date_to)
        if self.request_date_from and self.request_date_to and not self.request_unit_half:
            delta = (to - fr)
            if delta.days < 0:
                self.request_date_to = self.request_date_from

            self._compute_dates(fr, to)
            self.number_of_days = len(self.leave_date_ids.filtered(lambda p: p.payroll_period_id))
        else:
            if self.request_unit_half:
                self.request_date_to = self.request_date_from
                self.number_of_days = 0.5
                self._compute_dates(fr, fr)
            else:
                self.number_of_days = 0

    @api.multi
    def action_draft(self):
        self.leave_date_ids.write({'approve': False})
        self.leave_balance = self.leave_allocation_id.leave_balance
        self.state = 'draft'

    @api.multi
    def action_confirm(self):
        self._check_pay_period()
        self._compute_leave_duration()
        self.state = 'confirm'

    @api.multi
    def action_for_approval(self):
        self._check_pay_period()
        self._compute_leave_duration()
        self.state = 'for_approval'

    @api.multi
    def action_approve(self):
        self.leave_date_ids.write({'approve': True})
        self._check_pay_period()
        self._compute_leave_duration()
        self.state = 'approve'

    @api.multi
    def action_cancel(self):
        self.leave_date_ids.write({'approve': False})
        self.leave_balance = self.leave_allocation_id.leave_balance
        self.state = 'cancel'

    @api.multi
    def _check_pay_period(self):
        for ld in self.leave_date_ids:
            if not ld.payroll_period_id:
                raise ValidationError(_("'%s' must have payroll period assigned" % (ld.date).strftime("%m/%d/%Y")))

    @api.multi
    def _compute_leave_duration(self):
        for obj in self:
            if not obj.absence:
                if obj.number_of_days > obj.leave_balance:
                    raise ValidationError(_('Leave duration must not be greater to remaining leaves'))
        return True


class LeaveRequestDate(models.Model):
    _name = 'hr.leave.date'
    _order = 'date'

    date = fields.Date()
    leave_id = fields.Many2one('hr.leave', string='Leave Request')
    employee_id = fields.Many2one(related='leave_id.employee_id', model='hr.employee', store=True)
    approve = fields.Boolean(default=False)
    payroll_period_id = fields.Many2one('hr.payroll.period', string='Payroll Period')


class LeaveAllocationMultiple(models.TransientModel):
    _name = 'leave.allocation.multiple'
    _rec_name = 'fiscal_year_id'

    STATE = [
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('validate', 'Approved')
    ]

    fiscal_year_id = fields.Many2one('account.fiscal.year', string='Fiscal Year', required=True)
    valid_from = fields.Date(default=date.today().strftime('%Y-01-01'), required=True)
    valid_to = fields.Date(default=date.today().strftime('%Y-12-31'), required=True)
    leave_type_id = fields.Many2one('hr.leave.type', string='Leave Type', required=True)
    number_of_days = fields.Float(string='Number of Days', required=True, default=5)
    convertible_leave = fields.Float(required=True, default=0)
    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Employees', required=True)
    state = fields.Selection(STATE, default='draft', required=True)

    @api.onchange('fiscal_year_id')
    def onchange_fiscal_year(self):
        self.valid_from = None
        self.valid_to = None
        if self.fiscal_year_id:
            self.valid_from = self.fiscal_year_id.date_from
            self.valid_to = self.fiscal_year_id.date_to

    def create_allocation(self):
        if not self.employee_ids:
            raise ValidationError(_('Employees must not be empty'))

        if self.number_of_days <= 0:
            raise ValidationError(_('Number of days must be greater to zero'))

        obj_leave_alloc = self.env['hr.leave.allocation']
        for emp in self.employee_ids:
            vals = {
                'employee_id': emp.id,
                'fiscal_year_id': self.fiscal_year_id.id,
                'holiday_status_id': self.leave_type_id.id,
                'valid_from': self.valid_from,
                'valid_to': self.valid_to,
                'number_of_days': self.number_of_days,
                'convertible_leave': self.convertible_leave,
                'state': self.state
            }
            new_alloc = obj_leave_alloc.create(vals)
            new_alloc.accumulated_leave = new_alloc._get_unused_leaves()


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.one
    def _compute_leave_allocation(self):
        self.leave_allocation = self.env['hr.leave.allocation'].search_count([
                ('employee_id', '=', self.id),
                ('state', 'in', ('draft', 'confirm', 'validate'))
            ])

    leave_allocation = fields.Integer(string='Leave Allocation', compute='_compute_leave_allocation')


class LeaveAllocationState(models.TransientModel):
    _name = 'leave.allocation.state'

    @api.multi
    def _get_leave_allocations(self):
        active_ids = self._context.get('active_ids')
        return [(6, 0, active_ids)]
    
    leave_allocation_ids = fields.Many2many(comodel_name='hr.leave.allocation', string='Allocations', default=_get_leave_allocations)
    state = fields.Selection(ALLOC_STATE, default='draft')

    def change_state(self):
        obj_att = self.env['hr.leave.allocation']
        if self.leave_allocation_ids:
            for alloc in self.leave_allocation_ids:
                if self.state == 'draft':
                    alloc.action_draft()
                elif self.state == 'confirm':
                    alloc.action_confirm()
                elif self.state == 'validate':
                    alloc.action_approve()
                elif self.state == 'expire':
                    alloc.action_expire()
                elif self.state == 'refuse':
                    alloc.action_refuse()
        else:
            raise ValidationError(_('Allocations must not be empty'))


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    accumulated_annual_leave = fields.Boolean()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            accumulated_annual_leave=bool(self.env['ir.config_parameter'].sudo().get_param(
                'leaves.accumulated_annual_leave'))
            )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'leaves.accumulated_annual_leave', self.accumulated_annual_leave)
