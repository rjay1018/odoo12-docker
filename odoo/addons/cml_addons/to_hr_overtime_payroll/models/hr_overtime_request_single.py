from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

import logging

_logger = logging.getLogger(__name__)


class HrOvertimeRequestSingle(models.Model):
    _name = 'hr.overtime.request_single'
    _inherit = ['abstract.hr.overtime.request']

    @api.model
    def _get_default_employee(self):
        HREmployee = self.env['hr.employee']

        employee_id = HREmployee.search([('user_id', '=', self.env.user.id)], limit=1)
        if not employee_id:
            employee_id = HREmployee.search([('address_home_id', '=', self.env.user.partner_id.id)], limit=1)

        return employee_id and employee_id.id or False

    request_line_ids = fields.One2many('hr.overtime.line', 'overtime_request_id',
                                   string='Overtime Request Lines', readonly=True, states={'draft': [('readonly', False)]},
                                   copy=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', help='The employee for whom this request is', default=_get_default_employee,
                                  readonly=True, states={'draft': [('readonly', False)]}, copy=True, required=True)
    approving_user_id = fields.Many2one('res.users', string='Approver', compute='_get_approving_user_id', store=True, index=True,
                                  help='The user who is assigned to take approval action on this record')
    can_confirm = fields.Boolean(string='Can Confirm', compute='_compute_can_confirm')
    can_reconfirm = fields.Boolean(string='Can Confirm', compute='_compute_can_reconfirm')
    can_approve = fields.Boolean(string='Can Approve', compute='_compute_can_approve')
    hr_contract_id = fields.Many2one('hr.contract', string='Contract', store=True, related='employee_id.contract_id')
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id')
    job_id = fields.Many2one('hr.job', string='Job', related='employee_id.job_id')

    @api.constrains('approving_user_id')
    def _check_approving_user_id(self):
        for r in self:
            if not r.approving_user_id:
                raise ValidationError(_('No Overtime Approval User found for this overtime approval request.'
                                        ' It\'s probably the employee profile has not been setup fully (i.e. no department specified, no manager specified).\n'
                                        'In case this is for an employee without any manager, he must be granted with Overtime Manager rights to declare an overtime request.'))

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            if self.request_line_ids:
                for line in self.request_line_ids:
                    line.employee_id = self.employee_id

    @api.depends('employee_id')
    def _get_approving_user_id(self):
        for r in self:
            if r.employee_id:
                if r.employee_id.overtime_approving_user_id:
                    r.approving_user_id = r.employee_id.overtime_approving_user_id
                elif r.employee_id.user_id and r.employee_id.user_id.has_group('to_hr_overtime_payroll.group_hr_overtime_manager'):
                    r.approving_user_id = r.employee_id.user_id
                else:
                    r.approving_user_id = False

    def _compute_can_confirm(self):
        for r in self:
            if r.state != 'draft':
                r.can_confirm = False
            else:
                user = self.env.user
                if user.id == r.employee_id.user_id.id or user.has_group('to_hr_overtime_payroll.group_hr_overtime_manager') or (user.has_group('to_hr_overtime_payroll.group_hr_overtime_user') and user.id == r.approving_user_id.id):
                    r.can_confirm = True
                else:
                    r.can_confirm = False

    def _compute_can_reconfirm(self):
        for r in self:
            if r.state != 'refused':
                r.can_confirm = False
            else:
                user = self.env.user
                if user.id == r.employee_id.user_id.id or user.has_group('to_hr_overtime_payroll.group_hr_overtime_manager') or (user.has_group('to_hr_overtime_payroll.group_hr_overtime_user') and user.id == r.approving_user_id.id):
                    r.can_reconfirm = True
                else:
                    r.can_reconfirm = False

    def _compute_can_approve(self):
        for r in self:
            if r.state != 'confirmed':
                r.can_approve = False
            else:
                user = self.env.user
                if user.has_group('to_hr_overtime_payroll.group_hr_overtime_manager') or (user.has_group('to_hr_overtime_payroll.group_hr_overtime_user') and user.id == r.approving_user_id.id):
                    r.can_approve = True
                else:
                    r.can_approve = False

    def _generate_name(self):
        return self.env['ir.sequence'].next_by_code('overtime.request_single') or '/'

    @api.multi
    def action_confirm(self):
        for r in self:
            if not r.request_line_ids:
                raise UserError(_('You must declare your overtime before you can confirm the request.'))

            if not r.can_confirm:
                raise UserError(_('You can only either confirm your own overtime requests or your direct subordinate\'s requests.'
                              ' Or, you must be a manager of this application to confirm every request you want'))

        draft_line_ids = self.mapped('request_line_ids').filtered(lambda line: line.state == 'draft')
        if draft_line_ids:
            draft_line_ids.action_confirm()
        super(HrOvertimeRequestSingle, self).action_confirm()

    @api.multi
    def action_reconfirm(self):
        refused_line_ids = self.mapped('request_line_ids').filtered(lambda line: line.state == 'refused')
        if refused_line_ids:
            refused_line_ids.action_reconfirm()
        super(HrOvertimeRequestSingle, self).action_reconfirm()

    @api.multi
    def action_approve(self):
        for r in self:
            if not r.can_approve:
                raise UserError(_('You are not authorised to approve this request. Only the following people can approve it:\n'
                                '* Your direct manager %s\n'
                                '* The head/manager of your human resource management')
                              % (r.approving_user_id and '(who may be ' + r.approving_user_id.name + ')' or ''))
            if not r.request_line_ids:
                raise UserError(_('There is no overtime declaration for approval.'))

        self.mapped('request_line_ids').action_approve()
        super(HrOvertimeRequestSingle, self).action_approve()

    @api.multi
    def action_done(self):
        request_line_ids = self.mapped('request_line_ids').filtered(lambda l: l.state == 'approved')
        if request_line_ids:
            request_line_ids.action_done()
        super(HrOvertimeRequestSingle, self).action_done()

    @api.multi
    def action_cancel(self):
        request_line_ids = self.mapped('request_line_ids').filtered(lambda l: l.state != 'canceled')
        if request_line_ids:
            request_line_ids.action_cancel()
        super(HrOvertimeRequestSingle, self).action_cancel()

    @api.multi
    def unlink(self):
        request_line_ids = self.mapped('request_line_ids')
        if request_line_ids:
            request_line_ids.unlink()
        return super(HrOvertimeRequestSingle, self).unlink()

