from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
import datetime
import time


class Loan(models.Model):
    _name = 'hr.loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Loan Request'
    _order = 'date_request desc'

    STATE = [
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('cancel', 'Cancelled')
    ]

    @api.multi
    @api.depends('loan_line_ids')
    def _compute_loan_amount(self):
        for obj in self:
            total_paid = sum(line.amount for line in obj.loan_line_ids)
            obj.paid_amount = total_paid
            obj.balance_amount = obj.loan_amount - total_paid

    @api.model
    def _get_post_journal_entry(self):
        return bool(self.env['ir.config_parameter'].sudo().get_param('loans.post_loan_journal_entries'))

    @api.model
    def _default_employee(self):
        if self.env.uid > 2:
            return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        else:
            return None

    name = fields.Char(string='Loan #', default='/', readonly=True)
    date_request = fields.Date(string='Date Request', default=lambda *d: datetime.date.today(), required=True)
    date_approve = fields.Date(string='Date Approve', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee, required=True)
    department_id = fields.Many2one(related='employee_id.department_id', model='hr.department', string='Department', store=True)
    parent_department_id = fields.Many2one('hr.department', 'Parent Department')
    job_position_id = fields.Many2one(related='employee_id.job_id', model='hr.job', string='Job Position')
    contract_id = fields.Many2one('hr.contract', string='Contract')

    payment_start = fields.Date(string='Payment Start', required=True, default=lambda *d: datetime.date.today())
    payment_end = fields.Date(string='Payment End', required=True, default=lambda *d: datetime.date.today() + relativedelta(months=12))
    
    other_assets_account_id = fields.Many2one('account.account', string='Other Assets Account')
    liability_account_id = fields.Many2one('account.account', string='Liability Account')
    journal_id = fields.Many2one('account.journal', string='Journal')
    
    company_id = fields.Many2one('res.company', 'Company', readonly=True, default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id)
    
    loan_amount = fields.Float(string='Loan Amount', required=True)
    monthly_payment = fields.Float(string='Payment per Period', required=True)
    paid_amount = fields.Float(string='Total Paid Amount', compute='_compute_loan_amount', store=True)
    balance_amount = fields.Float(string='Balance Amount', compute='_compute_loan_amount', store=True)
    loan_line_ids = fields.One2many('hr.loan.line', 'loan_id', string='Loan Line', index=True)
    move_id = fields.Many2one('account.move', string='Accounting Entry')
    journal_entry = fields.Boolean(default=_get_post_journal_entry)
    reason = fields.Text()

    state = fields.Selection(STATE, string='State', default='draft', track_visibility='onchange', copy=False)

    @api.onchange('employee_id')
    def onchange_employee(self):
        self.other_assets_account_id = None
        self.liability_account_id = None
        self.journal_id = None

        self.contract_id = self.env['hr.contract'].get_active_contract(self.employee_id, False)

        self.parent_department_id = None
        dept = self.department_id if self.department_id else self.contract_id.department_id
        if dept:
            if dept.parent_id:
                if not dept.parent_id.parent_id:
                    self.parent_department_id = dept.parent_id.id
                else:
                    self.parent_department_id = dept.parent_id.parent_id.id
            else:
                self.parent_department_id = dept.id

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].get('hr.loan.seq') or '/'
        return super(Loan, self).create(values)

    def _get_max_loan_amount(self, new_loan_amt):
        t_approved_loan = 0
        loans = self.search([('employee_id', '=', self.employee_id.id), ('state', '=', 'approve')])
        t_approved_loan = sum(l.loan_amount for l in loans)

        if self.employee_id.max_loan > 0:
            if (t_approved_loan + new_loan_amt) > self.employee_id.max_loan:
                raise ValidationError(_('This employee has reached its maximum loanable amount of %s' % (
                    '{:1,.2f}'.format(self.employee_id.max_loan))))
        return True

    def action_submit(self):
        if self.monthly_payment > self.loan_amount:
            raise ValidationError(_('Payment per Period must be equal or less than loanable amount'))

        if self.journal_entry:
            if not self.liability_account_id or not self.other_assets_account_id or not self.journal_id:
                raise ValidationError('Other Assets Account, Liability Account and Journal must be present to continue')

        self._compute_loan_amount()
        self._get_max_loan_amount(self.loan_amount)
        self.state = 'submit'
        self.date_approve = datetime.date.today()

    def _create_salary_structure(self):
        if not self.contract_id:
            raise ValidationError(_('Employee must have running contract to continue'))

        vals = {
            'date': self.date_approve,
            'adjustment_id': self.adjustment_id.id,
            'period_type': self.period_type,
            'loan_id': self.id,
            'amount': self.monthly_payment
        }
        self.contract_id.structure_ids = [(0, 0, vals)]

    @api.multi
    def action_approve(self):
        for loan in self:
            if loan.loan_amount <= 0 or loan.monthly_payment <= 0:
                raise ValidationError(_('Loan Amount or Payment per Period must not be zero'))

            loan._create_salary_structure()

            if loan.journal_entry:
                if not loan.liability_account_id or not loan.other_assets_account_id or not loan.journal_id:
                    raise ValidationError('Other Assets Account, Liability Account and Journal must be present to continue')

                amount = loan.loan_amount
                loan_name = loan.employee_id.name
                reference = loan.adjustment_id.name
                journal_id = loan.journal_id.id
                debit_account_id = loan.other_assets_account_id.id
                credit_account_id = loan.liability_account_id.id
                debit_vals = {
                    'name': loan_name,
                    'account_id': debit_account_id,
                    'journal_id': journal_id,
                    'date': loan.date_approve,
                    'debit': amount > 0.0 and amount or 0.0,
                    'credit': amount < 0.0 and -amount or 0.0,
                    'loan_id': loan.id,
                }
                credit_vals = {
                    'name': loan_name,
                    'account_id': credit_account_id,
                    'journal_id': journal_id,
                    'date': loan.date_approve,
                    'debit': amount < 0.0 and -amount or 0.0,
                    'credit': amount > 0.0 and amount or 0.0,
                    'loan_id': loan.id,
                }
                vals = {
                    'name': reference + ' of ' + loan_name,
                    'narration': loan_name,
                    'ref': reference,
                    'journal_id': journal_id,
                    'date': loan.date_approve,
                    'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
                }
                move = self.env['account.move'].create(vals)
                move.post()
                loan.move_id = move.id
            loan.state = 'approve'

    def action_cancel(self):
        self.state = 'cancel'

    def action_draft(self):
        if not self.loan_line_ids:
            if self.move_id:
                self._delete_move_entry()
            self._remove_contract_loan_line()
            self.state = 'draft'
        else:
            raise ValidationError(_('This action is not possible for loans that has payment transactions.'))

    def _remove_contract_loan_line(self):
        self.contract_id.structure_ids.filtered(lambda l: l.loan_id.id == self.id).unlink()

    def _delete_move_entry(self, move=None):
        move = self.move_id if not move else move
        move_line_ids = move.sudo().mapped('line_ids')
        reconcile_ids = []
        if move_line_ids:
            reconcile_ids = move_line_ids.sudo().mapped('id')
            reconcile_lines = self.env['account.partial.reconcile'].sudo().search(
                ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
            if reconcile_lines:
                reconcile_lines.sudo().unlink()
        move_line_ids.sudo().write({'state': 'draft'})
        move.sudo().write({'state': 'draft'})
        move_line_ids.sudo().unlink()
        move.sudo().unlink()

    @api.multi
    def unlink(self):
        for loan in self:
            if loan.state not in ('draft', 'cancel'):
                raise ValidationError('You cannot delete a loan which is not in draft or cancelled state')
        return super(Loan, self).unlink()


class InstallmentLine(models.Model):
    _name = 'hr.loan.line'
    _order = 'date DESC'
    _description = 'Installment Line'

    date = fields.Date(string='Payment Date', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    amount = fields.Float(string='Amount', required=True)
    paid = fields.Boolean(string='Paid')
    loan_id = fields.Many2one('hr.loan', string='Loan')
    payslip_id = fields.Many2one('hr.payslip', string='Payslip', ondelete='cascade')

    @api.multi
    @api.constrains('loan_id', 'payslip_id')
    def _check_duplicate(self):
        for obj in self:
            args = [('loan_id', '=', obj.loan_id.id), ('payslip_id', '=', obj.payslip_id.id)]
            if len(self.search(args)) > 1:
                raise ValidationError(_('Loan payment from %s for Loan #: %s already exists' % (obj.payslip_id.name, obj.loan_id.name)))


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.one
    def _compute_employee_loans(self):
        self.loan_count = self.env['hr.loan'].search_count([('employee_id', '=', self.id)])

    loan_count = fields.Integer(string='Loan Count', compute='_compute_employee_loans')
