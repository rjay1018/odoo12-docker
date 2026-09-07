from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from ..constants import STATES
from datetime import timedelta
from odoo.addons.mail.models import mail_template


class HrOvertimeLine(models.Model):
    _name = 'hr.overtime.line'
    _description = 'HR Overtime Line'
    _order = 'employee_id, start_time, end_time, id'

    @api.model
    def _get_default_employee(self):
        HREmployee = self.env['hr.employee']
        employee_id = HREmployee.search([('user_id', '=', self.env.user.id)], limit=1)

        if not employee_id:
            employee_id = HREmployee.search([('address_id', '=', self.env.user.partner_id.id)], limit=1)
            if not employee_id:
                # sudo() is required since the address_home_id requires hr.group_hr_user
                # See: https://github.com/tvtma/odoo/blob/5f35e97e917b3a15ac5e4202d6811fb0c30caa42/addons/hr/models/hr.py#L113
                employee_id = HREmployee.sudo().search([('address_home_id', '=', self.env.user.partner_id.id)], limit=1)

        return employee_id or False

    @api.model
    def _get_default_start_time(self):
        recent = False
        if self.employee_id:
            recent = self.search([('employee_id', '=', self.employee_id.id)], order='end_time desc', limit=1)

        if recent:
            start_time = recent.end_time
        else:
            start_time = fields.Datetime.now()

        return start_time

    @api.model
    def _get_default_end_time(self):
        recent_end_time = self._get_default_start_time()
        return recent_end_time + timedelta(minutes=30)

    name = fields.Char(string='Name', compute='_compute_name')

    state = fields.Selection(STATES, string='Status', readonly=True, copy=False, track_visibility='onchange', default="draft", index=True)

    employee_id = fields.Many2one('hr.employee', string='Employee', index=True, default=_get_default_employee,
                                  readonly=True, states={'draft': [('readonly', False)]})

    overtime_request_id = fields.Many2one('hr.overtime.request_single', string='Overtime Reference',
                                           ondelete='cascade', index=True, copy=False, required=True)

    hr_contract_id = fields.Many2one('hr.contract', string='Applied Contract', index=True)

    resource_calendar_id = fields.Many2one('resource.calendar', string='Working Schedule', compute='_compute_res_calendar', store=True)

    overtime_rule_id = fields.Many2one('hr.overtime.rule', string='OT Rule', index=True, compute='_compute_overtime_rule_id', store=True)

    start_time = fields.Datetime('Start Time', required=True, readonly=True, default=_get_default_start_time,
                                 states={'draft': [('readonly', False)], 'refused': [('readonly', False)]})

    end_time = fields.Datetime('End Time', required=True, readonly=True, default=_get_default_end_time,
                               states={'draft': [('readonly', False)], 'refused': [('readonly', False)]})

    worked_hours = fields.Float(string="Worked Hours", compute="_compute_worked_hours", store=True)

    department_id = fields.Many2one('hr.department', string='Department', readonly=True, compute='_compute_job_dept', store=True)
    job_id = fields.Many2one('hr.job', string='Job Title', readonly=True, compute='_compute_job_dept', store=True)

    approving_user_id = fields.Many2one('res.users', string='Approver', compute='_get_approving_user_id',
                                  help='The user who is assigned to take approval action on this record')

    approved_by = fields.Many2one('res.users', string='Approved By', help='The user who took approval action', readonly=True)
    payslip_ot_line_id = fields.Many2one('hr.payslip.overtime.line', string='Payslip Overtime Line', index=True, ondelete='set null')
    payslip_id = fields.Many2one('hr.payslip', string='Payslip', index=True, readonly=True, ondelete='set null')

    rate = fields.Float(string='Rate (%)', compute='_compute_rate', store=True, help="The allowance rate in percentage which is computed"
                        " automatically based on the corresponding Overtime Rule's rate. In case no rate defined for the Overtime Rule,"
                        " 100% will be applied.")
    reason_id = fields.Many2one('hr.overtime.reason', string='Reason', readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]})
    description = fields.Text(string='Description')

    work_day_type_id = fields.Many2one('work.day.type', string='Work Day Type', compute='_compute_work_day_type', store=True,
                                       help="This field provides additional information on the work day type that the overtime is on."
                                       " It is helpful when you want to consider work day type is an additional factor for overtime"
                                       " allowance calculation.")

    _sql_constraints = [
        ('time_check',
         "CHECK (start_time < end_time)",
         "The start time must be anterior to the end time."),
    ]

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.overtime_request_id:
            if not self.overtime_request_id.employee_id:
                raise UserError(_('Please select an employee first!'))
            self.employee_id = self.overtime_request_id.employee_id
            if self.employee_id.contract_id:
                self.hr_contract_id = self.employee_id.contract_id
                self.resource_calendar_id = self.hr_contract_id.resource_calendar_id and self.hr_contract_id.resource_calendar_id or False
            if not self.resource_calendar_id:
                self.resource_calendar_id = self.employee_id.calendar_id

    @api.depends('start_time', 'end_time')
    def _compute_work_day_type(self):
        WorkDayType = self.env['work.day.type']
        for r in self:
            if r.start_time and r.end_time:
                work_day_type_id = WorkDayType.search([
                    ('date_from', '<=', r.start_time.date()),
                    ('date_to', '>=', r.end_time.date())], limit=1) or self.env.ref('to_hr_work_day_type.normal_work_day')
            else:
                work_day_type_id = self.env.ref('to_hr_work_day_type.normal_work_day')

            r.work_day_type_id = work_day_type_id

    @api.constrains('start_time', 'end_time', 'employee_id', 'resource_calendar_id', 'state', 'work_day_type_id')
    def _check_time(self):
        for r in self:
            is_holiday = r.work_day_type_id and r.work_day_type_id.is_holiday or False
            start_time = fields.Datetime.from_string(r.start_time)
            end_time = fields.Datetime.from_string(r.end_time)

            local_start_time = fields.Datetime.context_timestamp(r, start_time)
            local_end_time = fields.Datetime.context_timestamp(r, end_time)

            if local_start_time.date() != local_end_time.date():
                raise UserError(_('You are not allowed to input an overtime interval that crossing more than one day.'
                                  ' Please re-input the line having the following information:\n'
                                  '* Employee: %s\n'
                                  '* Start Time: %s\n'
                                  '* End Time: %s\n') % (r.employee_id.name, r._format_tz(r.start_time), r._format_tz(r.end_time)))

            # check if overlapping other lines
            if r.state not in ('draft', 'canceled'):
                overlapped_line_id = self.search([
                    ('id', '!=', r.id),
                    ('employee_id', '=', r.employee_id.id),
                    ('state', 'not in', ('draft', 'canceled')),
                    ('start_time', '<', r.end_time),
                    ('end_time', '>', r.start_time)], limit=1)
                if overlapped_line_id:
                    raise UserError(_("You are not allowed to submit the overtime interval (%s ~ %s) which is overlapping"
                                      " with an existed one (%s ~ %s) that was declared in the request %s."
                                      " Please re-input the line having the following information:\n"
                                      "* Employee: %s\n"
                                      "* Start Time: %s\n"
                                      "* End Time: %s")
                                      % (r._format_tz(r.start_time),
                                         r._format_tz(r.end_time),
                                         overlapped_line_id._format_tz(overlapped_line_id.start_time), overlapped_line_id._format_tz(overlapped_line_id.end_time),
                                         overlapped_line_id.overtime_request_id.name,
                                         r.employee_id.name, r._format_tz(r.start_time), r._format_tz(r.end_time)))

            # checking with resource calendar
            if r.resource_calendar_id and not r.reason_id.allow_working_schedule_overlap and not is_holiday:
                is_overlaping, attendances = r.resource_calendar_id.is_overlaping(local_start_time, local_end_time)
                if is_overlaping and r.state in ('draft', 'confirmed'):
                    info_str = ''
                    for attendance in attendances:
                        info_str += '* %s\n' % (attendance.name)
                    raise ValidationError(_("The input overtime interval specified by '%s' and '%s' is overlapping the normal working schedule '%s' of the employee '%s'.\n"
                                            "The following working hours are overlapped:\n"
                                            "%s\n"
                                            "You may need to select a reason that allows overlapping to bypass the check.")
                                          % (r._format_tz(r.start_time), r._format_tz(r.end_time), r.resource_calendar_id.name, r.employee_id.name, info_str))

            # checking overtime rule crossing
            is_crossing, first_match, second_match = r.env['hr.overtime.rule'].is_crossing(local_start_time, local_end_time, is_holiday)
            if is_crossing:
                raise ValidationError(_("You've inputed an overtime interval specified by %s and %s that is crossing the following overtime rules:\n"
                                        "* %s\n"
                                        "* %s\n"
                                        "Please split the interval into multiple ones to ensure that each will not be crossing two or more overtime rules")
                                        % (r._format_tz(r.start_time), r._format_tz(r.end_time), first_match.display_name, second_match.display_name))

    def _format_tz(self, dt, tz=False, format=False):
        return mail_template.format_tz(self.env, dt, tz=tz, format=format)

    def _build_display_name(self):
        start_time = self._format_tz(self.start_time)
        end_time = self._format_tz(self.end_time)
        name = "[%s - %s] %s" % (start_time, end_time, self.employee_id.name) if self.employee_id else "[%s - %s]" % (start_time, end_time)
        return name

    @api.multi
    @api.depends('start_time', 'end_time', 'employee_id')
    def _compute_name(self):
        for r in self:
            r.name = r._build_display_name()

    def _get_approving_user_id(self):
        for r in self:
            if r.employee_id:
                r.approving_user_id = r.employee_id.overtime_approving_user_id
            else:
                r.approving_user_id = False

    @api.multi
    @api.depends('employee_id')
    def _compute_job_dept(self):
        for r in self:
            data = {'department_id': False, 'job_id': False}
            if r.employee_id:
                if r.employee_id.department_id:
                    data['department_id'] = r.employee_id.department_id.id
                if r.employee_id.job_id:
                    data['job_id'] = r.employee_id.job_id.id
            r.update(data)

    @api.depends('overtime_rule_id')
    def _compute_rate(self):
        for r in self:
            if r.overtime_rule_id:
                r.rate = r.overtime_rule_id.rate
            else:
                r.rate = 100.0

    def _get_resource_calendar(self, employee, contract=False):
        resource_calendar = False
        if not contract:
            contract = employee.contract_id or False

        if contract and contract.resource_calendar_id:
            resource_calendar = contract.resource_calendar_id
        elif employee.resource_calendar_id:
            resource_calendar = employee.resource_calendar_id

        return resource_calendar

    @api.depends('employee_id', 'hr_contract_id')
    def _compute_res_calendar(self):
        for r in self:
            if r.employee_id:
                r.resource_calendar_id = r._get_resource_calendar(r.employee_id, r.hr_contract_id or r.employee_id.contract_id)

    @api.depends('start_time', 'end_time', 'employee_id')
    def _compute_worked_hours(self):
        for r in self:
            start_datetime = fields.Datetime.from_string(r.start_time)
            end_datetime = fields.Datetime.from_string(r.end_time)
            r.worked_hours = ((end_datetime - start_datetime).total_seconds()) / 3600.0

    @api.multi
    @api.depends('start_time', 'end_time', 'employee_id', 'resource_calendar_id', 'state', 'work_day_type_id')
    def _compute_overtime_rule_id(self):
        OvertimeRule = self.env['hr.overtime.rule']
        for r in self:
            start_time = fields.Datetime.from_string(r.start_time)
            end_time = fields.Datetime.from_string(r.end_time)

            local_start_time = fields.Datetime.context_timestamp(r, start_time)
            local_end_time = fields.Datetime.context_timestamp(r, end_time)

            # find match
            is_holiday = r.work_day_type_id and r.work_day_type_id.is_holiday or False
            first_match = OvertimeRule.is_crossing(local_start_time, local_end_time, is_holiday)[1] or False

            r.overtime_rule_id = first_match

    @api.multi
    def action_confirm(self):
        for r in self:
            if r.state != 'draft':
                raise UserError(_("You cannot confirm while the status is not Draft."))
        self.write({'state': 'confirmed'})

    @api.multi
    def action_reconfirm(self):
        for r in self:
            if r.state != 'refused':
                raise UserError(_("You cannot confirm while the status is not Refused."))
        self.write({'state': 'confirmed'})

    @api.multi
    def action_refuse(self):
        for r in self:
            if r.state not in ('approved', 'confirmed', 'refused'):
                raise UserError(_('You cannot refuse a request line whose state is other than \'approved\''))

            if r.payslip_ot_line_id:
                raise ValidationError(_('You cannot refuse an overtime line while it is linked to a payslip'))

        self.write({
            'state': 'refused',
            })

    @api.multi
    def action_approve(self):
        self.write({
            'approved_by': self.env.user.id,
            'state': 'approved',
            })

    @api.multi
    def action_re_approve(self):
        self.write({
            'state': 'approved',
            })

    @api.multi
    def action_draft(self):
        for r in self:
            if r.state != 'canceled':
                raise UserError(_("You cannot set the overtime interval specified by '%s' and '%s' for the employee %s"
                                  " to Draft state while it is not in Cancelled state")
                                  % (r._format_tz(r.start_time), r._format_tz(r.end_time), r.employee_id.name))
        self.write({'state': 'draft'})

    @api.multi
    def action_done(self):
        for r in self:
            if r.state != 'approved':
                raise UserError(_("The overtime declaration %s ~ %s must be in the state of Approved before it can be set as Done.")
                                % (r.start_time, r.end_time))
        self.write({'state': 'done'})
        can_done_overtime_request_ids = self.mapped('overtime_request_id').filtered(lambda req: all(line_id.state == 'done' for line_id in req.request_line_ids))
        if can_done_overtime_request_ids:
            can_done_overtime_request_ids.action_done()

    @api.multi
    def action_cancel(self):
        for r in self:
            if r.state not in ('confirmed', 'approved', 'refused'):
                raise UserError(_("You cannot cancel the overtime interval specified by '%s' and '%s' and for the employee %s"
                                  " while its state is neither Confirmed nor Approved nor Refused.")
                                  % (r._format_tz(r.start_time), r._format_tz(r.end_time), r.employee_id.name))
            if r.payslip_id:
                raise UserError(_("You cannot cancel the overtime interval specified by '%s' and '%s' and for the employee %s"
                                  " while it is still referred by the payslip %s.")
                                  % (r._format_tz(r.start_time), r._format_tz(r.end_time), r.employee_id.name, r.payslip_id.name))

        self.write({'state': 'canceled'})

    @api.multi
    def unlink(self):
        for r in self:
            if r.state != 'draft':
                raise UserError(_('You cannot delete a request which is not in draft state'))
        return super(HrOvertimeLine, self).unlink()
