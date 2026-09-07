from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
import datetime
import time


class Canteen(models.Model):
    _name = 'hr.canteen'
    _rec_name = 'employee_id'
    _order = 'date desc'

    STATE = [
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('paid', 'Paid')
    ]

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get('hr.canteen.seq') or '/'
        return super(Canteen, self).create(vals)

    @api.multi
    def unlink(self):
        for loan in self:
            if loan.state != 'draft':
                raise ValidationError('You cannot delete a loan which is not in draft state')
        return super(Canteen, self).unlink()

    @api.model
    def _get_post_journal_entry(self):
        return bool(self.env['ir.config_parameter'].sudo().get_param('loans.post_canteen_journal_entries'))

    name = fields.Char(string="Charge #", default='/')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    contract_id = fields.Many2one('hr.contract', string='Contract')
    department_id = fields.Many2one(related='employee_id.department_id', model='hr.department', string='Department', store=True)
    parent_department_id = fields.Many2one('hr.department', 'Parent Department')
    loan_amount = fields.Float(string='Charge Amount', required=True)
    date = fields.Date(required=True, default=lambda *d: datetime.date.today())
    state = fields.Selection(STATE, default='draft')
    liability_account_id = fields.Many2one('account.account', string='Liability Account')
    other_assets_account_id = fields.Many2one('account.account', string='Other Assets Account')
    journal_id = fields.Many2one('account.journal', string='Journal')
    move_id = fields.Many2one('account.move', string='Accounting Entry')
    journal_entry = fields.Boolean(default=_get_post_journal_entry)

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

        if self.journal_entry:
            canteen_adj_id = self.env.ref('ph_payroll_computation.canteen_loan', None).id
            if canteen_adj_id:
                adj = self.env['hr.payroll.adjustment'].browse(canteen_adj_id)
                self.other_assets_account_id = adj.ga_other_assets_account_id.id if adj.ga_other_assets_account_id else None
                self.liability_account_id = adj.ga_liability_account_id.id if adj.ga_liability_account_id else None
                self.journal_id = adj.journal_id.id if adj.journal_id else None

    def action_confirm(self):
        for loan in self:
            if loan.journal_entry:
                if not loan.liability_account_id or not loan.other_assets_account_id or not loan.journal_id:
                    raise ValidationError('Other Assets Account, Liability Account and Journal must be present to continue')

                amount = loan.loan_amount
                loan_name = loan.employee_id.name
                reference = 'Canteen Charges'
                journal_id = loan.journal_id.id
                debit_account_id = loan.other_assets_account_id.id
                credit_account_id = loan.liability_account_id.id

                debit_vals = {
                    'name': loan_name,
                    'account_id': debit_account_id,
                    'journal_id': journal_id,
                    'date': loan.date,
                    'debit': amount > 0.0 and amount or 0.0,
                    'credit': amount < 0.0 and -amount or 0.0,
                    'loan_id': loan.id,
                }
                credit_vals = {
                    'name': loan_name,
                    'account_id': credit_account_id,
                    'journal_id': journal_id,
                    'date': loan.date,
                    'debit': amount < 0.0 and -amount or 0.0,
                    'credit': amount > 0.0 and amount or 0.0,
                    'loan_id': loan.id,
                }
                vals = {
                    'name': reference + ' of ' + loan_name,
                    'narration': loan_name,
                    'ref': reference,
                    'journal_id': journal_id,
                    'date': loan.date,
                    'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
                }
                move = self.env['account.move'].create(vals)
                move.post()
                loan.move_id = move.id
            loan.state = 'confirm'

    def action_paid(self):
        self.state = 'paid'

    def action_draft(self):
        if self.move_id:
            self.env['hr.loan']._delete_move_entry(self.move_id)
        self.state = 'draft'
