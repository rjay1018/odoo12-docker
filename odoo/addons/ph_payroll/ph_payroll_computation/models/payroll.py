from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp
from odoo.addons.ph_payroll_contract.models.contract import EmployeeContract as contract
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import date, datetime, time
from lxml import etree
import os
import base64

import logging
_logger = logging.getLogger(__name__)


PAYSLIP_STATE = [
    ('draft', 'Draft'),
    ('confirm', 'Confirmed'),
    ('done', 'Done'),
    ('cancel', 'Cancelled'),
    ('refund', 'Refunded')
]

PERIOD_TYPE = [
    ('1st_2nd', '1st Half & 2nd Half'),
    ('1st', '1st Half'),
    ('2nd', '2nd Half')
]

class PayrollRegister(models.Model):
    _name = 'hr.payslip.run'
    _inherit = ['hr.payslip.run', 'mail.thread', 'mail.activity.mixin']
    _order = 'payroll_period_id'
    _description = 'Payroll Registers'

    STATE = [
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('close', 'Closed'),
        ('cancel', 'Cancelled')
    ]

    @api.model
    def _get_cash_bank_account(self):
        return int(self.env['ir.config_parameter'].sudo().get_param('payslip.payroll_cash_bank_account_id'))

    @api.model
    def _get_salary_journal(self):
        obj_journal = self.env['account.journal']
        journal = obj_journal.search([('code', '=', 'SAL'), ('name', '=', 'Salary'), ('type', '=', 'general')])
        return journal.id if journal else None

    @api.multi
    @api.depends('slip_ids.gross_pay', 'slip_ids.net_pay', 'slip_ids.state', 'slip_ids.credit_note')
    def _compute_total(self):
        for obj in self:
            late = ut = ot = nd = pr = 0
            wtax = oe = od = 0
            gross = net = cnt = 0
            for slip in obj.slip_ids.filtered(lambda s: not s.credit_note and s.state not in ('cancel', 'refund')):
                late += slip.late_amount
                ut += slip.undertime_amount
                ot += slip.overtime_amount
                nd += slip.night_diff_amount
                pr += slip.total_premium
                wtax += slip.wtax
                oe += slip.other_earning
                od += slip.other_deduction
                gross += slip.gross_pay
                net += slip.net_pay
                cnt += 1

            obj.total_late = late
            obj.total_undertime = ut
            obj.total_overtime = ot
            obj.total_night_diff = nd
            obj.total_premium = pr
            obj.total_wtax = wtax
            obj.total_earning = oe
            obj.total_deduction = od
            obj.total_gross = gross
            obj.total_net = net
            obj.slip_count = cnt

    @api.model
    def _get_post_journal_entry(self):
        return bool(self.env['ir.config_parameter'].sudo().get_param('payslip.post_slip_journal_entries'))

    payroll_schedule = fields.Selection(contract.PAYROLL_SCHEDULE, required=True, default='3_sm')
    date = fields.Date('Payroll Date', required=True, default=lambda *d: date.today())
    cash_bank_account_id = fields.Many2one('account.account', string='Cash in Bank Account', default=_get_cash_bank_account)
    journal_id = fields.Many2one('account.journal', 'Salary Journal', default=_get_salary_journal, required=False)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id, required=True)
    date_from = fields.Date(string='Date From', required=False)
    date_to = fields.Date(string='Date To', required=False)
    state = fields.Selection(STATE, default='draft')
    payroll_period_id = fields.Many2one('hr.payroll.period', string='Payroll Period', required=True)
    total_late = fields.Float(compute=_compute_total, digits=dp.get_precision('Payroll'), store=True)
    total_undertime = fields.Float(compute=_compute_total, digits=dp.get_precision('Payroll'), store=True)
    total_overtime = fields.Float(compute=_compute_total, digits=dp.get_precision('Payroll'), store=True)
    total_night_diff = fields.Float(compute=_compute_total, digits=dp.get_precision('Payroll'), store=True)
    total_premium = fields.Float(compute=_compute_total, digits=dp.get_precision('Payroll'), store=True)
    total_wtax = fields.Float(compute=_compute_total, digits=dp.get_precision('Payroll'), string='Total W-Tax', store=True)
    total_earning = fields.Float(compute=_compute_total, digits=dp.get_precision('Payroll'), store=True)
    total_deduction = fields.Float(compute=_compute_total, digits=dp.get_precision('Payroll'), store=True)
    total_gross = fields.Float(compute=_compute_total, digits=dp.get_precision('Payroll'), string='TOTAL GROSS', store=True)
    total_net = fields.Float(compute=_compute_total, digits=dp.get_precision('Payroll'), string='TOTAL NET', store=True)
    slip_count = fields.Integer(compute=_compute_total, string='Payslips', store=True)
    convertible_leave = fields.Boolean()
    release_13th_pay = fields.Boolean('13th Month Pay')
    journal_entry = fields.Boolean(default=_get_post_journal_entry)
    slip_ids = fields.One2many('hr.payslip', 'payslip_run_id', string='Payslips', readonly=True, states={'draft': [('readonly', False)]},
        domain=[('state', 'not in', ('cancel', 'refund')), ('credit_note', '=', False)])

    @api.onchange('journal_id')
    def onchange_journal(self):
        if self.journal_id:
            self.company_id = self.journal_id.company_id.id
        else:
            self.company_id = self.env.user.company_id.id

    @api.multi
    def unlink(self):
        for obj in self:
            if obj.state != 'draft':
                raise ValidationError('You cannot delete a payroll register which is not in draft state')
        return super(PayrollRegister, self).unlink()

    def action_recompute_sheet(self):
        if len(self.slip_ids) < 1:
            raise ValidationError(_('No payslips to recompute'))

        for slip in self.slip_ids.filtered(lambda s: not s.credit_note and s.state not in ('cancel', 'refund')):
            slip.convertible_leave = self.convertible_leave
            slip.release_13th_pay = self.release_13th_pay
            slip.compute_sheet()

    def action_confirm(self):
        if len(self.slip_ids) < 1:
            raise ValidationError(_('No payslips to confirm'))
        
        for slip in self.slip_ids.filtered(lambda s: not s.credit_note and s.state not in ('cancel', 'refund')):
            slip.action_confirm()

        self.state = 'confirm'

    def action_cancel(self):
        for slip in self.slip_ids.filtered(lambda s: not s.credit_note and s.state not in ('cancel', 'refund')):
            slip.action_cancel()

        self.state = 'cancel'

    def action_draft(self):
        for slip in self.slip_ids.filtered(lambda s: not s.credit_note and s.state not in ('cancel', 'refund')):
            slip.action_payslip_draft()

        self.state = 'draft'

    def action_validate(self):
        done_slip = 0
        for slip in self.slip_ids.filtered(lambda s: not s.credit_note and s.state not in ('cancel', 'refund')):
            if slip.state == 'confirm':
                slip.action_validate()

            if slip.state == 'done':
                done_slip += 1

        if done_slip > 0 and done_slip == len(self.slip_ids.filtered(lambda s: not s.credit_note and s.state not in ('cancel', 'refund'))):
            self.state = 'close'

    def _get_partner_address(self, p):
        obj_partner = self.env['res.partner']
        return obj_partner._get_partner_address(p)

    def _get_payroll_sign(self, manager=False):
        obj_emp = self.env['hr.employee']
        if manager:
            field = 'manager'
        else:
            field = 'payroll_master'
        emp = obj_emp.search([(field, '!=', False)], limit=1)
        return emp.name or ''

    no = 0
    def get_no(self):
        self.no += 1
        return self.no

    def generate_bank_doc(self):
        vals = {}
        HEADER = CONTENT = FOOTER = YE3 = ''
        total_net = emp_cnt = 0

        account_no = str(self.env['ir.config_parameter'].sudo().get_param('payslip.company_bank_account_no'))
        obj_attach = self.env['ir.attachment']

        payroll_date = fields.Date.to_string(self.date)
        y, m, d = payroll_date.split('-')
        YE3 = "YE3" + y + m + d
        fname = "YE3" + m + d + y[2:] + "01.txt"

        try:
            HEADER = "H         " + account_no + "       " + YE3 + "\n"

            for slip in self.slip_ids.filtered(lambda s: not s.credit_note and s.state not in ('cancel', 'refund')):
                if not slip.credit_note:
                    if slip.employee_id.bank_account_id:
                        emp_cnt += 1
                        total_net += slip.net_pay

                        CONTENT += str(slip.employee_id.bank_account_id.acc_number) + '      ' + str('{:.2f}'.format(slip.net_pay)) + '\n'

            FOOTER = 'T        ' + str(emp_cnt) + str('{:.2f}'.format(total_net)) + "\n"

            datas = base64.b64encode(bytes(HEADER + CONTENT + FOOTER, 'utf-8'))
            vals['datas'] = datas
            vals['datas_fname'] = fname
            vals['name'] = YE3
            vals['res_model'] = self._name
            vals['res_id'] = self.id

            args = [('res_model', '=', self._name), ('res_id', '=', self.id)]
            attach = obj_attach.search(args)
            if not attach:
                attach = obj_attach.create(vals)
            else:
                attach.write(vals)
        except Exception as e:
            raise ValidationError(_(e))

    def _report_data(self):
        obj_att = self.env['hr.attendance']
        data = {
            'print_on': ''
        }
        data['print_on'] = obj_att._localize_dt(datetime.now()).strftime('%m/%d/%Y @ %I:%M:%S %p')
        return data


class Payslip(models.Model):
    _inherit = 'hr.payslip'
    _order = 'payroll_period_id, employee_id'

    @api.onchange('payslip_run_id')
    def onchange_register(self):
        self.state = 'draft'
        if self.payslip_run_id:
            self.payroll_schedule = self.payslip_run_id.payroll_schedule
            self.payroll_period_id = self.payslip_run_id.payroll_period_id.id
            self.date_from = self.payslip_run_id.payroll_period_id.period_fr
            self.date_to = self.payslip_run_id.payroll_period_id.period_to
            self.date = self.payslip_run_id.date
            self.journal_id = self.payslip_run_id.journal_id.id
            self.cash_bank_account_id = self.payslip_run_id.cash_bank_account_id.id
            self.convertible_leave = self.payslip_run_id.convertible_leave
            self.release_13th_pay = self.payslip_run_id.release_13th_pay

    @api.onchange('payroll_schedule')
    def onchange_pay_sched(self):
        self.employee_id = None
        domain = [('id', '>', 1)]
        if self.payroll_schedule:
            obj_contract = self.env['hr.contract']
            domain = [('id', 'in', obj_contract._get_employees_with_this_pay_sched(self.payroll_schedule))]
        return {'domain': {'employee_id': domain}}

    def _get_period_name(self):
        period = self.payroll_period_id
        date_fr = period.period_fr
        date_to = period.period_to
        fr = str(date_fr).split('-')
        to = str(date_to).split('-')
        period_fr = str(date(int(fr[0]), int(fr[1]), int(fr[2])).strftime('%b %d'))
        period_to = str(date(int(to[0]), int(to[1]), int(to[2])).strftime('%b %d, %Y'))
        return '%s (%s - %s)' % (period.period_type, period_fr, period_to)

    def _slip_name(self, emp_name):
        return _('Payslip of %s for - %s') % (emp_name or '-', self._get_period_name())

    @api.multi
    @api.onchange('employee_id', 'contract_id')
    def onchange_employee(self, recompute=False):
        if not recompute:
            for obj in self:
                obj.name = ''
                employee = obj.employee_id
                obj.work_days = 0
                obj.basic_pay = 0

                if obj.payroll_period_id:
                    obj.name = self._slip_name(employee.name)

                obj.contract_id = obj.env['hr.contract'].get_active_contract(employee)
                obj.company_id = employee.company_id

                obj.parent_department_id = None
                dept = obj.contract_id.department_id
                if dept:
                    if dept.parent_id:
                        if not dept.parent_id.parent_id:
                            obj.parent_department_id = dept.parent_id.id
                        else:
                            obj.parent_department_id = dept.parent_id.parent_id.id
                    else:
                        obj.parent_department_id = dept.id

                    if obj.parent_department_id and obj.parent_department_id.salary_wage_account_id:
                        obj.salary_wage_account_id = obj.parent_department_id.salary_wage_account_id.id

    @api.onchange('payroll_period_id')
    def onchange_payroll_period(self):
        if self.payroll_period_id and self.employee_id:
            if not self.name:
                self.name = self._slip_name(self.employee_id.name)

    @api.onchange('parent_department_id')
    def onchange_parent_department(self):
        if self.parent_department_id and self.parent_department_id.salary_wage_account_id:
            self.salary_wage_account_id = self.parent_department_id.salary_wage_account_id.id

    def _compute_contract(self):
        period_type = self.payroll_period_id.period_type
        if not period_type:
            raise ValidationError(_('Payroll Period must be selected first to compute salary structure, premiums and tax'))

        self.slip_structure_ids.filtered(lambda a: a.structure_line_id).unlink()

        adj_cashadv = self.env.ref('ph_payroll_computation.adj_cashadv').id
        adj_comp_loan = self.env.ref('ph_payroll_computation.adj_comp_loan').id

        for s in self.contract_id.structure_ids.filtered(lambda a: a.state == 'open'):
            if s.period_type == period_type or s.period_type == '1st_2nd':
                tax_amt = 0
                if s.adjustment_id.ceiling_amount > 0:
                    if s.amount > s.adjustment_id.ceiling_amount:
                        tax_amt = s.amount - s.adjustment_id.ceiling_amount

                amount = s.amount
                if self.final_pay:
                    if s.loan_id.adjustment_id.id in (adj_cashadv, adj_comp_loan):
                        amount = s.loan_id.balance_amount

                vals = {
                    'structure_line_id': s.id,
                    'adjustment_id': s.adjustment_id.id,
                    'loan_id': s.loan_id.id if s.loan_id else None,
                    'amount': amount,
                    'ceiling_amount': s.adjustment_id.ceiling_amount,
                    'taxable_amount': tax_amt
                }
                self.slip_structure_ids = [(0, 0, vals)]

    @api.one
    @api.depends('contract_id')
    def _compute_premiums(self):
        self.ensure_one()
        obj_hdmf = self.env['hdmf.table']
        obj_phic = self.env['phic.table']
        obj_sss = self.env['sss.table']
        obj_prem_tax_config = self.env['hr.premiums.tax.config']

        if not self.journal_id:
            self.journal_id = self._get_salary_journal()

        self.hdmf_ee = self.hdmf_er = 0
        self.phic_ee = self.phic_er = 0
        self.sss_ee = self.sss_er = 0
        self.sss_ee_mpf = self.sss_er_mpf = 0

        hdmf_ee = obj_hdmf._get_hdmf(self.wage)['ee']
        hdmf_er = obj_hdmf._get_hdmf(self.wage)['er']
        phic_ee = obj_phic._get_phic(self.wage)['ee']
        phic_er = obj_phic._get_phic(self.wage)['er']
        sss_ee = obj_sss._get_sss(self.wage)['ee']
        sss_er = obj_sss._get_sss(self.wage)['er']
        sss_ee_mpf = obj_sss._get_sss(self.wage)['mpf_ee']
        sss_er_mpf = obj_sss._get_sss(self.wage)['mpf_er']

        hdmf_period_type = obj_prem_tax_config._get_premium_tax_data('hdmf').period_type
        phic_period_type = obj_prem_tax_config._get_premium_tax_data('phic').period_type
        sss_period_type = obj_prem_tax_config._get_premium_tax_data('sss').period_type

        payroll_period_type = self.payroll_period_id.period_type

        if self.payroll_schedule == '2_w': # Weekly
            if self.contract_id.hdmf:
                if self.contract_id.hdmf_amount == 0:
                    self.hdmf_ee = hdmf_ee / 4
                else:
                    self.hdmf_ee = self.contract_id.hdmf_amount / 4
                self.hdmf_er = hdmf_er / 4
            if self.contract_id.phic:
                if self.contract_id.phic_amount == 0:
                    self.phic_ee = phic_ee / 4
                    self.phic_er = phic_er / 4
                else:
                    self.phic_ee = self.contract_id.phic_amount / 4
                    self.phic_er = self.contract_id.phic_amount / 4
            if self.contract_id.sss:
                if self.contract_id.sss_amount == 0:
                    self.sss_ee = sss_ee / 4
                    self.sss_ee_mpf = sss_ee_mpf / 4
                else:
                    self.sss_ee = self.contract_id.sss_amount / 4
                self.sss_er = sss_er / 4
                self.sss_er_mpf = sss_er_mpf / 4

        elif self.payroll_schedule == '3_sm': # Semi-Monthly
            if self.contract_id.hdmf:
                if self.contract_id.hdmf_amount == 0:
                    if hdmf_period_type == '1st_2nd':
                        self.hdmf_ee = hdmf_ee / 2
                        self.hdmf_er = hdmf_er / 2
                    else:
                        if hdmf_period_type == payroll_period_type:
                            self.hdmf_ee = hdmf_ee
                            self.hdmf_er = hdmf_er
                else:
                    if hdmf_period_type == '1st_2nd':
                        self.hdmf_ee = self.contract_id.hdmf_amount / 2
                        self.hdmf_er = hdmf_er / 2
                    else:
                        if hdmf_period_type == payroll_period_type:
                            self.hdmf_ee = self.contract_id.hdmf_amount
                            self.hdmf_er = hdmf_er

            if self.contract_id.phic:
                if self.contract_id.phic_amount == 0:
                    if phic_period_type == '1st_2nd':
                        self.phic_ee = phic_ee / 2
                        self.phic_er = phic_er / 2
                    else:
                        if phic_period_type == payroll_period_type:
                            self.phic_ee = phic_ee
                            self.phic_er = phic_er
                else:
                    if phic_period_type == '1st_2nd':
                        self.phic_ee = self.contract_id.phic_amount / 2
                        self.phic_er = self.contract_id.phic_amount / 2
                    else:
                        if phic_period_type == payroll_period_type:
                            self.phic_ee = self.contract_id.phic_amount
                            self.phic_er = self.contract_id.phic_amount

            if self.contract_id.sss:
                if self.contract_id.sss_amount == 0:
                    if sss_period_type == '1st_2nd':
                        self.sss_ee = sss_ee / 2
                        self.sss_er = sss_er / 2
                        self.sss_ee_mpf = sss_ee_mpf / 2
                        self.sss_er_mpf = sss_er_mpf / 2
                    else:
                        if sss_period_type == payroll_period_type:
                            self.sss_ee = sss_ee
                            self.sss_er = sss_er
                            self.sss_ee_mpf = sss_ee_mpf
                            self.sss_er_mpf = sss_er_mpf
                else:
                    if sss_period_type == '1st_2nd':
                        self.sss_ee = self.contract_id.sss_amount / 2
                        self.sss_er = sss_er / 2
                        self.sss_ee_mpf = sss_ee_mpf / 2
                        self.sss_er_mpf = sss_er_mpf / 2
                    else:
                        if sss_period_type == payroll_period_type:
                            self.sss_ee = self.contract_id.sss_amount
                            self.sss_er = sss_er
                            self.sss_ee_mpf = sss_ee_mpf
                            self.sss_er_mpf = sss_er_mpf

        elif self.payroll_schedule == '4_m': # Monthly
            if self.contract_id.hdmf:
                if self.contract_id.hdmf_amount == 0:
                    self.hdmf_ee = hdmf_ee
                else:
                    self.hdmf_ee = self.contract_id.hdmf_amount
                self.hdmf_er = hdmf_er
            if self.contract_id.phic:
                if self.contract_id.phic_amount == 0:
                    self.phic_ee = phic_ee
                    self.phic_er = phic_er
                else:
                    self.phic_ee = self.contract_id.phic_amount
                    self.phic_er = self.contract_id.phic_amount
            if self.contract_id.sss:
                if self.contract_id.sss_amount == 0:
                    self.sss_ee = sss_ee
                    self.sss_ee_mpf = sss_ee_mpf
                else:
                    self.sss_ee = self.contract_id.sss_amount
                self.sss_er = sss_er
                self.sss_er_mpf = sss_er_mpf

        self.total_premium = (self.hdmf_ee + self.phic_ee + self.sss_ee + self.sss_ee_mpf)

    @api.model
    def _get_salary_journal(self):
        return self.env['hr.payslip.run']._get_salary_journal()

    @api.model
    def _get_cash_bank_account(self):
        return int(self.env['ir.config_parameter'].sudo().get_param('payslip.payroll_cash_bank_account_id'))

    @api.model
    def _get_post_journal_entry(self):
        return bool(self.env['ir.config_parameter'].sudo().get_param('payslip.post_slip_journal_entries'))

    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payroll Register', copy=True)
    payroll_schedule = fields.Selection(contract.PAYROLL_SCHEDULE, required=True, default='3_sm')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    salary_wage_account_id = fields.Many2one('account.account', string='Salaries & Wages Account')
    cash_bank_account_id = fields.Many2one('account.account', string='Cash in Bank Account', default=_get_cash_bank_account)
    journal_id = fields.Many2one('account.journal', 'Salary Journal', default=_get_salary_journal, required=False)
    currency_id = fields.Many2one(string='Currency', related='company_id.currency_id')
    wage_type = fields.Selection(related='contract_id.wage_type', store=True)
    # payroll_schedule = fields.Selection(related='contract_id.payroll_schedule', store=True)
    wage = fields.Monetary(related='contract_id.wage', string='Basic Wage', store=True)
    daily_pay = fields.Monetary(related='contract_id.daily_pay', string='Daily Pay', store=True)
    date = fields.Date('Payroll Date', required=True, default=lambda *d: date.today())
    payroll_period_id = fields.Many2one('hr.payroll.period', string='Payroll Period')
    work_days = fields.Float(string='Regular Worked Days', readonly=True)
    regular_holiday = fields.Float(string='Paid Reg. Holiday', readonly=True)
    regular_holiday_amount = fields.Float(string='Paid Reg. Holiday Amt.', readonly=True)

    paid_leave = fields.Float(string='Paid Leave', readonly=True)
    vacation_leave = fields.Float(readonly=True)
    vacation_leave_amount = fields.Float(string='Amount', readonly=True)
    sick_leave = fields.Float(readonly=True)
    sick_leave_amount = fields.Float(string='Amount', readonly=True)
    converted_leave_ids = fields.One2many('hr.leave.convert', 'payslip_id')

    unpaid_leave = fields.Float(string='Unpaid Leave/Absent', readonly=True)
    unpaid_leave_amount = fields.Float(string='Up. Leave/Absent Amt.', readonly=True)
    halfday = fields.Float(readonly=True)
    halfday_amount = fields.Float(string='Amount', readonly=True)
    absent = fields.Float(readonly=True)
    absent_amount = fields.Float(string='Amount', readonly=True)

    late = fields.Float(readonly=True)
    late_amount = fields.Float(digits=dp.get_precision('Payroll'), readonly=True)
    undertime = fields.Float(readonly=True)
    undertime_amount = fields.Float(digits=dp.get_precision('Payroll'), readonly=True)
    overtime = fields.Float(readonly=True)
    overtime_amount = fields.Float(digits=dp.get_precision('Payroll'), readonly=True)
    night_diff = fields.Float(string='Night Diff.', readonly=True)
    night_diff_amount = fields.Float(string='Night Diff. Amount', digits=dp.get_precision('Payroll'), readonly=True)
    
    other_taxable = fields.Float(digits=dp.get_precision('Payroll'), readonly=True)

    basic_pay = fields.Float(digits=dp.get_precision('Payroll'), string='BASIC PAY', readonly=True)
    cola_amount = fields.Float(digits=dp.get_precision('Payroll'), string='COLA', readonly=True)
    gross_pay = fields.Float(digits=dp.get_precision('Payroll'), string='GROSS TAXABLE', readonly=True)
    net_pay = fields.Float(digits=dp.get_precision('Payroll'), string='NET PAY', readonly=True)
    other_earning = fields.Float(digits=dp.get_precision('Payroll'), string='Other Earn. (Non-Tax)', readonly=True)
    other_deduction = fields.Float(digits=dp.get_precision('Payroll'), string='Other Deduction', readonly=True)
    wtax = fields.Float(digits=dp.get_precision('Payroll'), string='W-Tax', readonly=True)
    month_13th = fields.Float(digits=dp.get_precision('Payroll'), string='Amount', readonly=True)
    hdmf_ee = fields.Float(compute=_compute_premiums, digits=dp.get_precision('Payroll'), string='HDMF (EE)', store=True)
    hdmf_er = fields.Float(compute=_compute_premiums, digits=dp.get_precision('Payroll'), string='HDMF (ER)', store=True)
    phic_ee = fields.Float(compute=_compute_premiums, digits=dp.get_precision('Payroll'), string='PHIC (EE)', store=True)
    phic_er = fields.Float(compute=_compute_premiums, digits=dp.get_precision('Payroll'), string='PHIC (ER)', store=True)
    sss_ee = fields.Float(compute=_compute_premiums, digits=dp.get_precision('Payroll'), string='SSS (EE)', store=True)
    sss_er = fields.Float(compute=_compute_premiums, digits=dp.get_precision('Payroll'), string='SSS (ER)', store=True)
    sss_ee_mpf = fields.Float(compute=_compute_premiums, digits=dp.get_precision('Payroll'), string='SSS MPF (EE)', store=True)
    sss_er_mpf = fields.Float(compute=_compute_premiums, digits=dp.get_precision('Payroll'), string='SSS MPF (ER)', store=True)
    total_premium = fields.Float(compute=_compute_premiums, digits=dp.get_precision('Payroll'), string='Total Premium (EE)', store=True)
    slip_structure_ids = fields.One2many('hr.payslip.structure', 'slip_id', copy=True, domain=['|', ('active', '=', True), ('active', '=', False)], context={'active_test': False})
    # slip_structure_active = fields.Boolean(compute='_recompute_slip_structure', store=True) # dummy field to trigger changes in Slip Structure

    parent_department_id = fields.Many2one('hr.department', 'Parent Department')
    state = fields.Selection(PAYSLIP_STATE, index=True, copy=False, default='draft')
    overtime_summary_ids = fields.One2many('hr.overtime.summary', 'slip_id')
    leave_summary_ids = fields.One2many('hr.leave.summary', 'slip_id')
    refund_slip_id = fields.Many2one('hr.payslip', string='Refund Ref.')
    final_pay = fields.Boolean()
    convertible_leave = fields.Boolean()
    release_13th_pay = fields.Boolean('13th Month Pay')
    journal_entry = fields.Boolean(default=_get_post_journal_entry)

    spec_holiday_ot = fields.Float(digits=dp.get_precision('Payroll'))

    # @api.multi
    # @api.depends('slip_structure_ids')
    # def _recompute_slip_structure(self):
    #     for obj in self:
    #         for line in obj.slip_structure_ids:
    #             obj.compute_sheet(True)
    #             # obj.slip_structure_active = line.active
    #             _logger.info(_('HERE'))

    @api.onchange('final_pay')
    def onchange_final_pay(self):
        self.convertible_leave = False
        self.release_13th_pay = False
        if self.final_pay:
            self.convertible_leave = True
            self.release_13th_pay = True

    @api.constrains('employee_id', 'payroll_period_id')
    def _check_duplicate_slip(self):
        args = [
            ('employee_id', '=', self.employee_id.id),
            ('payroll_period_id', '=', self.payroll_period_id.id),
            ('credit_note', '=', False),
            ('state', 'not in', ('cancel', 'refund'))
        ]
        if len(self.search(args)) > 1:
            raise ValidationError(_('Duplicate payslip found for employee: %s and payroll period: %s' % (
                self.employee_id.name, self.payroll_period_id.name)))

    def _get_basic_pay(self):
        basic_pay = 0
        if self.contract_id.has_attendance:
            if self.wage_type == 'daily':
                # basic_pay = self.daily_pay * (self.work_days + self.regular_holiday)
                basic_pay = self.daily_pay * self.work_days
                basic_pay += self.daily_pay * self.paid_leave
            else:
                if self.payroll_schedule == '1_d':
                    basic_pay = self.daily_pay * 7
                elif self.payroll_schedule == '2_w':
                    basic_pay = self.wage / 4
                elif self.payroll_schedule == '3_sm':
                    basic_pay = self.wage / 2
                elif self.payroll_schedule == '4_m':
                    basic_pay = self.wage
        else:
            if self.payroll_schedule == '1_d':
                basic_pay = self.wage / 7
            elif self.payroll_schedule == '2_w':
                basic_pay = self.wage / 4
            elif self.payroll_schedule == '3_sm':
                basic_pay = self.wage / 2
            elif self.payroll_schedule == '4_m':
                basic_pay = self.wage
        return basic_pay + self._get_basic_pay_adjustment()

    def _get_basic_pay_adjustment(self):
        adj_basic = 0
        for s in self.slip_structure_ids.filtered(lambda a: a.adjustment_for == 'basic' and a.active):
            adj_basic += s.amount
        return adj_basic

    @api.multi
    def _compute_slip(self):
        for obj in self:
            oth_earn = oth_deduct = oth_tax = 0
            for ss in obj.slip_structure_ids:
                if ss.active:
                    if ss.adjustment_id.adjustment_type in ('allowance', 'otherbenefit', 'otherearning', 'refund', '13th_mo', '14th_mo'):
                        oth_earn += ss.amount
                    if ss.adjustment_id.adjustment_type in ('cashadvance', 'loan', 'otherdeduct'):
                        oth_deduct += ss.amount

                oth_tax += ss.taxable_amount

            obj.other_taxable = oth_tax
            obj.other_earning = oth_earn - oth_tax
            obj.other_deduction = oth_deduct

            premiums = 0
            if not obj.contract_id.premiums_excluded:
                premiums = obj.total_premium

            obj.basic_pay = obj._get_basic_pay()
            earn = obj.basic_pay + obj.cola_amount + obj.overtime_amount + obj.night_diff_amount + obj.regular_holiday_amount
            deduct = obj.late_amount + obj.undertime_amount + premiums #+ obj.halfday_amount
            obj.gross_pay = (earn - deduct) + obj.other_taxable
            obj.wtax = obj._compute_wtax()
            obj.net_pay = (obj.gross_pay + obj.other_earning) - (obj.wtax + obj.other_deduction)

            if obj.contract_id.premiums_excluded:
                obj.net_pay -= obj.total_premium

            obj.month_13th = self._get_13th_mo_comp(obj.basic_pay, {
                    'late': obj.late_amount,
                    'ut': obj.undertime_amount,
                    'ul': 0, #obj.halfday_amount, # instead of Unpaid Leave/Absent Amount
                    'ot': obj.overtime_amount,
                    'nd': obj.night_diff_amount
                })

    def _compute_wtax(self):
        wtax = 0
        gross_pay = self.gross_pay
        
        taxable_ot = bool(self.env['ir.config_parameter'].sudo().get_param('payslip.taxable_ot'))
        if not taxable_ot:
            gross_pay -= self.overtime_amount

        obj_prem_tax_config = self.env['hr.premiums.tax.config']
        wtax_period_type = obj_prem_tax_config._get_premium_tax_data('wtax').period_type

        if wtax_period_type == '1st_2nd':
            payroll_sched = '3_sm'
        else:
            payroll_sched = '4_m'
            gross_pay += self._get_previous_gross_tax_income()

        wtax_amount = self.env['wtax.table']._get_wtax(gross_pay, payroll_sched)

        if wtax_period_type == '1st_2nd':
            wtax = wtax_amount
        else:
            if wtax_period_type == self.payroll_period_id.period_type:
                wtax = wtax_amount
        return wtax

    def _get_previous_gross_tax_income(self):
        obj_slip = self.env['hr.payslip']
        prev_pay_period = self.env['hr.payroll.period']._get_previous_period(self.payroll_schedule, self.payroll_period_id)
        args = [('employee_id', '=', self.employee_id.id), ('payroll_period_id', '=', prev_pay_period.id)]
        slip = obj_slip.search_read(args, ['gross_pay'])
        return slip[0]['gross_pay'] if slip else 0

    @api.multi
    def unlink(self):
        for obj in self:
            if obj.state != 'draft':
                raise ValidationError('You cannot delete a payslip which is not in draft state')
        return super(Payslip, self).unlink()

    @api.multi
    def compute_sheet(self):
        for slip in self:
            if slip.state != 'draft':
                raise ValidationError(_('Payslip must be in draft state to continue'))
            if slip.contract_id and slip.contract_id.state != 'open':
                raise ValidationError(_('Employee contract must be active or running to continue'))
            if slip.payroll_schedule != slip.contract_id.payroll_schedule:
                raise ValidationError(_('Payroll schedule must be the same with employee contract'))

            slip.onchange_employee(True)
            slip._compute_contract()
            slip._compute_work_days()
            slip._compute_premiums()
            slip._compute_leave()
            slip._compute_ot()
            slip._compute_canteen_loan()
            slip._compute_adjustment()

            slip._compute_convertible_leave()
            slip._compute_13th_pay()

            slip._compute_slip()

    @api.multi
    def action_validate(self, other_premiums=[]):
        for obj in self:
            for ss in obj.slip_structure_ids.filtered(lambda s: s.adjustment_type != 'adjustment' and s.active):
                if ss.loan_id:
                    vals = {
                        'loan_id': ss.loan_id.id,
                        'payslip_id': obj.id,
                        'date': obj.date,
                        'amount': ss.amount if not obj.credit_note else -ss.amount
                    }
                    ss.loan_id.loan_line_ids = [(0, 0, vals)]

                if ss.structure_line_id and ss.structure_line_id.loan_id:
                    if ss.loan_id.paid_amount == ss.loan_id.loan_amount:
                        ss.structure_line_id.state = 'done'
                    elif ss.loan_id.paid_amount < ss.loan_id.loan_amount:
                        ss.structure_line_id.state = 'open'
                    else:
                        raise ValidationError(_("Payment to loan '%s' is greater than remaining balance. \n\nDifference: %s" % (
                            ss.loan_id.name, '{:1,.2f}'.format(abs(ss.loan_id.balance_amount)))))

                if ss.canteen_id:
                    ss.canteen_id.state = 'paid' if not obj.credit_note else 'confirm'

            if obj.convertible_leave:
                for a in obj.converted_leave_ids:
                    a.leave_allocation_id.converted = True
                    a.leave_allocation_id.payslip_id = obj.id


            if not obj.credit_note:
                # if bool(self.env['ir.config_parameter'].sudo().get_param('payslip.post_slip_journal_entries')):
                if obj.journal_entry:
                    obj._create_journal_entries(other_premiums)

            obj.state = 'done'

    def _create_journal_entries(self, other_premiums=[]):
        obj_prem_tax_config = self.env['hr.premiums.tax.config']

        salary_wages = (self.basic_pay + self.cola_amount) - (self.late_amount + self.undertime_amount) #+ self.halfday_amount)
        slip_name = self.employee_id.name
        reference = self.name
        journal_id = self.journal_id.id
        debit_account_id = self.salary_wage_account_id.id

        vals_list = []

        debit_vals = {
            'name': 'Basic Pay + COLA',
            'account_id': debit_account_id,
            'journal_id': journal_id,
            'date': self.date,
            'debit': salary_wages > 0.0 and salary_wages or 0.0,
            'credit': salary_wages < 0.0 and -salary_wages or 0.0
        }
        vals_list.append((0, 0, debit_vals))

        # Night Differential
        if self.night_diff_amount > 0:
            adj_nd_id = self.env.ref('ph_payroll_computation.adj_reg_night_diff', None).id
            if not adj_nd_id:
                raise ValidationError(_('Payroll Adjustment for Night Differential cannot be found'))

            obj_adjustment = self.env['hr.payroll.adjustment']
            adj_nd = obj_adjustment.browse(adj_nd_id)

            if not adj_nd.ga_extra_liability_account_id:
                raise ValidationError(_("Payroll Account for '%s' is not set" % (adj_nd.name)))
            account_id = adj_nd.ga_extra_liability_account_id.id

            if not adj_nd.journal_id:
                raise ValidationError(_("'%s' Journal is not set" % (adj_nd.name)))

            debit_vals = {
                'name': 'Night Differential',
                'account_id': account_id,
                'journal_id': journal_id,
                'date': self.date,
                'debit': self.night_diff_amount > 0.0 and self.night_diff_amount or 0.0,
                'credit': self.night_diff_amount < 0.0 and -self.night_diff_amount or 0.0
            }
            vals_list.append((0, 0, debit_vals))

        # Overtime Summary
        if self.overtime_summary_ids:
            for ot in self.overtime_summary_ids:
                if not ot.computation_id.ga_debit_account_id:
                    raise ValidationError(_("'%s' Debit Account is not set" % (ot.computation_id.name)))
                ot_debit_account_id = ot.computation_id.ga_debit_account_id.id
            
                if not ot.computation_id.journal_id:
                    raise ValidationError(_("'%s' Journal is not set" % (ot.computation_id.name)))

                debit_vals = {
                    'name': ot.computation_id.name,
                    'account_id': int(ot_debit_account_id),
                    'journal_id': int(ot.computation_id.journal_id.id),
                    'date': self.date,
                    'debit': ot.ot_amount > 0.0 and ot.ot_amount or 0.0,
                    'credit': ot.ot_amount < 0.0 and -ot.ot_amount or 0.0
                }
                vals_list.append((0, 0, debit_vals))

        # Salary Structure
        for ss in self.slip_structure_ids.filtered(lambda s: s.adjustment_type != 'adjustment' and s.active):
            if not ss.adjustment_id.ga_extra_liability_account_id:
                raise ValidationError(_("Payroll Account for '%s' is not set" % (ss.adjustment_id.name)))
            account_id = ss.adjustment_id.ga_extra_liability_account_id.id

            journal = ss.adjustment_id.journal_id
            if not journal:
                raise ValidationError(_("Journal for '%s' is not set" % (ss.adjustment_id.name)))

            debit_credit_vals = {
                'name': ss.adjustment_id.name,
                'account_id': account_id,
                'journal_id': journal.id,
                'date': ss.payment_date
            }

            # CREDIT
            if ss.adjustment_type in ('cashadvance', 'loan', 'otherdeduct'):
                debit_credit_vals['debit'] = ss.amount < 0.0 and -ss.amount or 0.0
                debit_credit_vals['credit'] = ss.amount > 0.0 and ss.amount or 0.0

            # DEBIT
            elif ss.adjustment_type in ('allowance', 'otherbenefit', 'otherearning', 'refund', '13th_mo', '14th_mo'):
                debit_credit_vals['debit'] = ss.amount > 0.0 and ss.amount or 0.0
                debit_credit_vals['credit'] = ss.amount < 0.0 and -ss.amount or 0.0

            vals_list.append((0, 0, debit_credit_vals))


        if self.wtax > 0:
            wtax_account = obj_prem_tax_config._get_premium_tax_data('wtax')
            if not wtax_account.ga_ee_credit_account_id:
                raise ValidationError(_('EE Credit Account for Withholding Tax is not set'))
            account_id = wtax_account.ga_ee_credit_account_id.id

            journal = wtax_account.journal_id
            if not journal:
                raise ValidationError(_('Journal for Withholding Tax is not set'))

            credit_vals = {
                'name': 'Withholding Tax',
                'account_id': account_id,
                'journal_id': journal.id,
                'date': self.date,
                'debit': self.wtax < 0.0 and -self.wtax or 0.0,
                'credit': self.wtax > 0.0 and self.wtax or 0.0
            }
            vals_list.append((0, 0, credit_vals))


        hdmf_account = obj_prem_tax_config._get_premium_tax_data('hdmf')
        phic_account = obj_prem_tax_config._get_premium_tax_data('phic')
        sss_account = obj_prem_tax_config._get_premium_tax_data('sss')

        hdmf_journal = hdmf_account.journal_id
        phic_journal = phic_account.journal_id
        sss_journal = sss_account.journal_id

        if not hdmf_journal:
            raise ValidationError(_('Journal for Pag-Ibig is not set'))
        if not phic_journal:
            raise ValidationError(_('Journal for Philhealth is not set'))
        if not sss_journal:
            raise ValidationError(_('Journal for SSS is not set'))


        # Employee Contribution
        if self.hdmf_ee > 0:
            if not hdmf_account.ga_ee_credit_account_id:
                raise ValidationError(_('EE Credit Account for Pag-Ibig is not set'))
            account_id = hdmf_account.ga_ee_credit_account_id.id

            credit_vals = {
                'name': 'Pag-Ibig Withheld from Employee',
                'account_id': account_id,
                'journal_id': hdmf_journal.id,
                'date': self.date,
                'debit': self.hdmf_ee < 0.0 and -self.hdmf_ee or 0.0,
                'credit': self.hdmf_ee > 0.0 and self.hdmf_ee or 0.0
            }
            vals_list.append((0, 0, credit_vals))

        if self.phic_ee > 0:
            if not phic_account.ga_ee_credit_account_id:
                raise ValidationError(_('EE Credit Account for Philhealth is not set'))
            account_id = phic_account.ga_ee_credit_account_id.id

            credit_vals = {
                'name': 'Philhealth Withheld from Employee',
                'account_id': account_id,
                'journal_id': phic_journal.id,
                'date': self.date,
                'debit': self.phic_ee < 0.0 and -self.phic_ee or 0.0,
                'credit': self.phic_ee > 0.0 and self.phic_ee or 0.0
            }
            vals_list.append((0, 0, credit_vals))

        if self.sss_ee > 0:
            if not sss_account.ga_ee_credit_account_id:
                raise ValidationError(_('EE Credit Account for SSS is not set'))
            account_id = sss_account.ga_ee_credit_account_id.id

            credit_vals = {
                'name': 'SSS Withheld from Employee',
                'account_id': account_id,
                'journal_id': sss_journal.id,
                'date': self.date,
                'debit': self.sss_ee < 0.0 and -self.sss_ee or 0.0,
                'credit': self.sss_ee > 0.0 and self.sss_ee or 0.0
            }
            vals_list.append((0, 0, credit_vals))

        if self.sss_ee_mpf > 0:
            if not sss_account.sss_ee_mpf_credit_account_id:
                raise ValidationError(_('EE Credit Account for SSS MPF is not set'))
            account_id = sss_account.sss_ee_mpf_credit_account_id.id

            credit_vals = {
                'name': 'SSS MPF Withheld from Employee',
                'account_id': account_id,
                'journal_id': sss_journal.id,
                'date': self.date,
                'debit': self.sss_ee_mpf < 0.0 and -self.sss_ee_mpf or 0.0,
                'credit': self.sss_ee_mpf > 0.0 and self.sss_ee_mpf or 0.0
            }
            vals_list.append((0, 0, credit_vals))


        # Employer Contribution
        if self.hdmf_er > 0:
            if not hdmf_account.ga_er_debit_account_id:
                raise ValidationError(_('ER Debit Account for Pag-Ibig is not set'))
            account_id = hdmf_account.ga_er_debit_account_id.id

            debit_vals = {
                'name': 'Pag-Ibig Premium Expense',
                'account_id': account_id,
                'journal_id': hdmf_journal.id,
                'date': self.date,
                'debit': self.hdmf_er > 0.0 and self.hdmf_er or 0.0,
                'credit': self.hdmf_er < 0.0 and -self.hdmf_er or 0.0
            }
            vals_list.append((0, 0, debit_vals))

            if not hdmf_account.er_credit_account_id:
                raise ValidationError(_('ER - Credit Account for Pag-Ibig is not set'))

            credit_vals = {
                'name': 'Accrued Pag-Ibig Contribution',
                'account_id': hdmf_account.er_credit_account_id.id,
                'journal_id': hdmf_journal.id,
                'date': self.date,
                'debit': self.hdmf_er < 0.0 and -self.hdmf_er or 0.0,
                'credit': self.hdmf_er > 0.0 and self.hdmf_er or 0.0
            }
            vals_list.append((0, 0, credit_vals))

        if self.phic_er > 0:
            if not phic_account.ga_er_debit_account_id:
                raise ValidationError(_('ER Debit Account for Philhealth is not set'))
            account_id = phic_account.ga_er_debit_account_id.id

            debit_vals = {
                'name': 'Philhealth Premium Expense',
                'account_id': account_id,
                'journal_id': phic_journal.id,
                'date': self.date,
                'debit': self.phic_er > 0.0 and self.phic_er or 0.0,
                'credit': self.phic_er < 0.0 and -self.phic_er or 0.0
            }
            vals_list.append((0, 0, debit_vals))

            if not phic_account.er_credit_account_id:
                raise ValidationError(_('ER - Credit Account for Philhealth is not set'))

            credit_vals = {
                'name': 'Accrued Philhealth Contribution',
                'account_id': phic_account.er_credit_account_id.id,
                'journal_id': phic_journal.id,
                'date': self.date,
                'debit': self.phic_er < 0.0 and -self.phic_er or 0.0,
                'credit': self.phic_er > 0.0 and self.phic_er or 0.0
            }
            vals_list.append((0, 0, credit_vals))

        if self.sss_er > 0:
            if not sss_account.ga_er_debit_account_id:
                raise ValidationError(_('ER Debit Account for SSS is not set'))
            account_id = sss_account.ga_er_debit_account_id.id

            debit_vals = {
                'name': 'SSS Premium Expense',
                'account_id': account_id,
                'journal_id': sss_journal.id,
                'date': self.date,
                'debit': self.sss_er > 0.0 and self.sss_er or 0.0,
                'credit': self.sss_er < 0.0 and -self.sss_er or 0.0
            }
            vals_list.append((0, 0, debit_vals))

            if not sss_account.er_credit_account_id:
                raise ValidationError(_('ER - Credit Account for SSS is not set'))

            credit_vals = {
                'name': 'Accrued SSS Contribution',
                'account_id': sss_account.er_credit_account_id.id,
                'journal_id': sss_journal.id,
                'date': self.date,
                'debit': self.sss_er < 0.0 and -self.sss_er or 0.0,
                'credit': self.sss_er > 0.0 and self.sss_er or 0.0
            }
            vals_list.append((0, 0, credit_vals))

        if self.sss_er_mpf > 0:
            if not sss_account.sss_er_mpf_debit_account_id:
                raise ValidationError(_('ER Debit Account for SSS MPF is not set'))
            account_id = sss_account.sss_er_mpf_debit_account_id.id

            debit_vals = {
                'name': 'SSS MPF Premium Expense',
                'account_id': account_id,
                'journal_id': sss_journal.id,
                'date': self.date,
                'debit': self.sss_er_mpf > 0.0 and self.sss_er_mpf or 0.0,
                'credit': self.sss_er_mpf < 0.0 and -self.sss_er_mpf or 0.0
            }
            vals_list.append((0, 0, debit_vals))

            if not sss_account.sss_er_mpf_credit_account_id:
                raise ValidationError(_('ER - Credit Account for SSS MPF is not set'))

            credit_vals = {
                'name': 'Accrued SSS MPF Contribution',
                'account_id': sss_account.sss_er_mpf_credit_account_id.id,
                'journal_id': sss_journal.id,
                'date': self.date,
                'debit': self.sss_er_mpf < 0.0 and -self.sss_er_mpf or 0.0,
                'credit': self.sss_er_mpf > 0.0 and self.sss_er_mpf or 0.0
            }
            vals_list.append((0, 0, credit_vals))

        # Other premiums/benefits
        if other_premiums:
            vals_list.extend(other_premiums)

        credit_vals = {
            'name': 'Net Pay',
            'account_id': self.cash_bank_account_id.id,
            'journal_id': journal_id,
            'date': self.date,
            'debit': self.net_pay < 0.0 and -self.net_pay or 0.0,
            'credit': self.net_pay > 0.0 and self.net_pay or 0.0
        }
        vals_list.append((0, 0, credit_vals))

        vals = {
            'name': slip_name,
            'narration': slip_name,
            'ref': reference,
            'journal_id': journal_id,
            'date': self.date,
            'line_ids': vals_list,
            'partner_id': self.employee_id.partner_id.id if self.employee_id.partner_id else None
        }

        move = self.env['account.move'].create(vals)
        move.post()
        self.move_id = move.id

    def _compute_canteen_loan(self):
        self.slip_structure_ids.filtered(lambda c: c.canteen_id).unlink()
        obj_canteen = self.env['hr.canteen']
        args = [
            ('employee_id', '=', self.employee_id.id),
            ('payroll_period_id', '=', self.payroll_period_id.id),
            ('state', '=', 'confirm')
            ]
        canteen = obj_canteen.search(args)
        if canteen:
            for loan in canteen:
                self.slip_structure_ids = [(0, 0, {
                        'canteen_id': loan.id,
                        'adjustment_id': self.env.ref('ph_payroll_computation.canteen_loan', None).id,
                        'amount': loan.loan_amount
                    })]

    def _compute_adjustment(self):
        basic = cola = late = undertime = ot = nd = wtax = earn = deduct = total_prem = 0

        for ss in self.slip_structure_ids.filtered(lambda a: not a.structure_line_id and a.active):
            if ss.adjustment_for == 'basic':
                basic += ss.amount
            elif ss.adjustment_for == 'cola':
                cola += ss.amount
            elif ss.adjustment_for == 'lwp':
                earn += ss.amount
            elif ss.adjustment_for == 'lwop':
                deduct += ss.amount
            elif ss.adjustment_for == 'late':
                late += ss.amount
            elif ss.adjustment_for == 'undertime':
                undertime += ss.amount
            elif ss.adjustment_for == 'ot':
                ot += ss.amount
            elif ss.adjustment_for == 'nd':
                nd += ss.amount
            elif ss.adjustment_for == 'wtax':
                wtax += ss.amount
            elif ss.adjustment_for == 'earn':
                earn += ss.amount
            elif ss.adjustment_for == 'deduct':
                deduct += ss.amount
            elif ss.adjustment_for in ('hdmf_prem', 'phic_prem', 'sss_prem'):
                total_prem += ss.amount

        self.basic_pay += basic
        self.cola_amount += cola
        self.late_amount += late
        self.undertime_amount += undertime
        self.overtime_amount += ot
        self.night_diff_amount += nd
        self.wtax += wtax
        self.other_earning += earn
        self.other_deduction += deduct
        self.total_premium += total_prem

        earn = self.basic_pay + self.cola_amount + self.overtime_amount + self.night_diff_amount
        deduct = self.late_amount + self.undertime_amount + self.total_premium
        self.gross_pay = earn - deduct
        self.net_pay = (self.gross_pay + self.other_earning) - (self.wtax + self.other_deduction)

    def _get_regular_holiday(self):
        obj_holiday = self.env['hr.holiday']
        obj_leave = self.env['hr.leave']
        fr = fields.Date.to_date(self.payroll_period_id.period_fr)
        to = fields.Date.to_date(self.payroll_period_id.period_to)
        dates = obj_leave._parse_dates(fr, to)
        reg_holidays = []
        for date in dates:
            args = [('date', '=', date), ('holiday_type', '=', 'regular'), ('active', '=', True)]
            days = obj_holiday.search(args)
            for day in days:
                if self.employee_id.id not in day.exempted_emp_ids.ids:
                    reg_holidays.append(fields.Date.to_date(day.date))
        return reg_holidays

    def _has_halfday_leave(self, date):
        obj_leave_date = self.env['hr.leave.date']
        args = [
            ('employee_id', '=', self.employee_id.id),
            ('payroll_period_id', '=', self.payroll_period_id.id),
            ('date', '=', date),
            ('approve', '=', True)
        ]
        leave = obj_leave_date.search(args)
        if leave:
            if leave.leave_id.request_unit_half:
                return True
        else: return False

    def _get_attendance(self):
        data = {
            'work_days': 0,
            'regular_holiday': 0,
            'late': 0,
            'undertime': 0,
            'night_diff': 0,
            'night_diff_amount': 0
        }

        obj_att = self.env['hr.attendance']
        args = [
            ('employee_id', '=', self.employee_id.id),
            ('payroll_period_id', '=', self.payroll_period_id.id),
            ('state', '=', 'validate')
        ]
        attendances = obj_att.search(args)
        for att in attendances:
            if self.contract_id.has_attendance:
                if not att.dayoff and not att.is_holiday:
                    if not att.regular_schedule:
                        data['work_days'] += 1
                    else:
                        data['work_days'] += 0.5

            if self.contract_id.has_attendance and self.contract_id.compute_late:
                data['late'] += att.late

            if self.contract_id.has_attendance and self.contract_id.compute_undertime:
                if not self._has_halfday_leave(att.localize_date):
                    if not att.is_holiday:
                        data['undertime'] += att.undertime

            if att.night_diff_rate_id:
                hourly_rate = self.daily_pay / 8.0
                data['night_diff'] += att.night_diff
                data['night_diff_amount'] += (hourly_rate * (att.night_diff_rate_id.rate - 1)) * att.night_diff

        if self.contract_id.paid_reg_holiday and self.wage_type == 'daily':
            reg_holidays = self._get_regular_holiday()
            if reg_holidays:
                atts = []
                for att in attendances:
                    if att.localize_date not in atts:
                        atts.append(att.localize_date)

                res = [rh for rh in reg_holidays if rh in atts]
                # data['work_days'] += (len(reg_holidays) - len(res))
                # data['regular_holiday'] += (len(reg_holidays) - len(res))
                data['regular_holiday'] += len(reg_holidays)

        if self.contract_id.has_attendance:
            if data['work_days'] == 0 and data['night_diff'] == 0:
                raise ValidationError(_("No attendance found for employee - '%s' for '%s' payroll period" % (
                    self.employee_id.name, self.payroll_period_id.name)))
        return data

    @api.multi
    def _compute_pass_slip(self):
        obj_pass_slip = self.env['hr.pass.slip']
        data = {
            'personal': 0,
            'official': 0
        }
        args = [
            ('payroll_period_id', '=', self.payroll_period_id.id),
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'approve')
        ]
        slips = obj_pass_slip.search(args)
        for slip in slips:
            if slip.transaction_type == 'p':        # Personal Transaction
                data['personal'] += slip.duration
            else:                                   # Official Transaction
                data['official'] += slip.duration
        return data

    def _compute_work_days(self):
        att = self._get_attendance()
        if att['work_days'] == 0:
            self.work_days = 0
            self.basic_pay = 0

        hourly_rate = self.daily_pay / 8.0

        ps = self._compute_pass_slip()
        undertime = (att['undertime'] + ps['personal']) - ps['official']

        self.work_days = att['work_days']
        self.regular_holiday = att['regular_holiday']
        self.regular_holiday_amount = att['regular_holiday'] * self.daily_pay
        self.late = att['late']
        self.late_amount = att['late'] * hourly_rate
        self.undertime = undertime
        self.undertime_amount = undertime * hourly_rate
        self.night_diff = att['night_diff']
        self.night_diff_amount = att['night_diff_amount']
        
        self.cola_amount = 0

        if self.work_days > 0:
            cola = self.contract_id.cola_amount
            if cola > 0:
                cola_hr_rate = cola / 8.0
                if self.undertime > 0:
                    self.cola_amount = ((self.work_days * 8) - self.undertime) * cola_hr_rate
                else:
                    self.cola_amount = (self.work_days * cola)

    @api.multi
    def _compute_leave(self):
        self.leave_summary_ids = None
        obj_leave_date = self.env['hr.leave.date']
        for slip in self:
            args = [
                ('employee_id', '=', slip.employee_id.id),
                ('payroll_period_id', '=', slip.payroll_period_id.id),
                ('approve', '=', True)
            ]
            leave_dates = obj_leave_date.search(args)

            paid = unpaid = 0
            halfday = absent = 0

            vl = sl = 0
            type_vl = self.env.ref('ph_payroll_leave.leave_type_vacation', None).id
            type_sl = self.env.ref('ph_payroll_leave.leave_type_sick', None).id

            for ld in leave_dates:
                leave_type = ld.leave_id.leave_allocation_id.holiday_status_id.leave_type
                if leave_type == 'paid':
                    if slip.contract_id.has_attendance:
                        if not ld.leave_id.request_unit_half:
                            paid += 1
                        else:
                            paid += 0.5
                elif leave_type == 'halfpaid':
                    if slip.contract_id.has_attendance:
                        paid += 0.5
                else:
                    if not ld.leave_id.request_unit_half:
                        unpaid += 1
                        absent += 1
                    else:
                        unpaid += 0.5
                        halfday += 0.5

                # if slip.contract_id.has_attendance:
                #     if ld.leave_id.holiday_status_id.id == type_vl:
                #         if leave_type == 'paid':
                #             if not ld.leave_id.request_unit_half:
                #                 vl += 1
                #             else:
                #                 vl += 0.5
                #     elif ld.leave_id.holiday_status_id.id == type_sl:
                #         if leave_type == 'paid':
                #             if not ld.leave_id.request_unit_half:
                #                 sl += 1
                #             else:
                #                 sl += 0.5

            leaves = []
            for l in leave_dates:
                if l.leave_id not in leaves:
                    leaves.append(l.leave_id)

            result = {}
            for l in leaves:
                res_item = result.get(l.holiday_status_id.id, None)
                if not res_item:
                    res_item = {
                        'holiday_status_id': l.holiday_status_id.id,
                        'leave_type': l.holiday_status_id.leave_type,
                        'duration': l.number_of_days,
                        'amount': l.number_of_days * slip.daily_pay
                    }
                else:
                    res_item['duration'] += l.number_of_days
                    res_item['amount'] += l.number_of_days * slip.daily_pay
                result[l.holiday_status_id.id] = res_item

            for k, v in result.items():
                vals = {
                    'holiday_status_id': int(k),
                    'leave_type': v['leave_type'],
                    'duration': v['duration'],
                    'amount': v['amount']
                }
                self.leave_summary_ids = [(0, 0, vals)]

            slip.paid_leave = paid
            slip.unpaid_leave = unpaid
            slip.unpaid_leave_amount = unpaid * slip.daily_pay
            # slip.vacation_leave = vl
            # slip.vacation_leave_amount = vl * slip.daily_pay
            # slip.sick_leave = sl
            # slip.sick_leave_amount = sl * slip.daily_pay
            slip.halfday = halfday
            slip.halfday_amount = halfday * slip.daily_pay
            slip.absent = absent
            slip.absent_amount = absent * slip.daily_pay

    @api.multi
    def _compute_convertible_leave(self):
        type_vl = self.env.ref('ph_payroll_leave.leave_type_vacation', None).id
        type_sl = self.env.ref('ph_payroll_leave.leave_type_sick', None).id
        adj_vlc_id = self.env.ref('ph_payroll_computation.vlc', None).id
        adj_slc_id = self.env.ref('ph_payroll_computation.slc', None).id

        for slip in self:
            slip.slip_structure_ids.filtered(lambda a: a.adjustment_id.id in (adj_slc_id, adj_vlc_id) and a.convertible_leave).unlink()
            if slip.convertible_leave:
                slip.converted_leave_ids = None
                args = [
                    ('employee_id', '=', slip.employee_id.id),
                    ('convertible_leave', '>', 0),
                    ('leave_balance', '>', 0),
                    ('state', '=', 'validate'),
                    ('converted', '=', False)
                ]
                allocations = self.env['hr.leave.allocation'].search(args)
                for alloc in allocations:
                    bal = alloc.convertible_leave
                    if alloc.leave_balance < alloc.convertible_leave:
                        bal = alloc.leave_balance

                    amt = slip.daily_pay * bal
                    vals = {
                        'convertible_leave': True,
                        'amount': amt
                    }
                    if alloc.holiday_status_id.id == type_vl:
                        vals['adjustment_id'] = adj_vlc_id
                    elif alloc.holiday_status_id.id == type_sl:
                        vals['adjustment_id'] = adj_slc_id

                    if 'adjustment_id' in vals:
                        slip.slip_structure_ids = [(0, 0, vals)]

                    slip.converted_leave_ids = [(0, 0, {
                            'leave_allocation_id': alloc.id,
                            'fiscal_year_id': alloc.fiscal_year_id.id,
                            'total_allocation': alloc.total_allocation,
                            'convertible_leave': alloc.convertible_leave,
                            'leave_count': alloc.leave_count,
                            'leave_balance': alloc.leave_balance,
                            'converted_days': bal,
                            'amount': amt
                        })]

    def _get_13th_mo_comp(self, basic_pay, vals):
        amt_13th = 0
        adj_13th = self.env.ref('ph_payroll_computation.13th_month')
        if adj_13th.adjustment_type == '13th_mo':
            if adj_13th.month13th_comp == 1:
                amt_13th = basic_pay
            elif adj_13th.month13th_comp == 2:
                amt_13th = (basic_pay - (vals['late'] + vals['ut'] + vals['ul']))
            else:
                amt_13th = ((basic_pay + vals['ot'] + vals['nd']) - (vals['late'] + vals['ut'] + vals['ul']))
        return amt_13th / 12

    def _compute_13th_pay(self):
        adj_13th_id = self.env.ref('ph_payroll_computation.13th_month').id
        self.slip_structure_ids.filtered(lambda s: s.adjustment_id.id == adj_13th_id and s.release_13th_pay).unlink()

        if self.release_13th_pay:
            current_basic_pay = self._get_basic_pay()

            if self._extract_date(self.payroll_period_id.period_fr)['month'] == 12:
                # If payroll period is december then add 2nd half basic pay if pay sched is semi-monthly or weekly
                # since 13th month should be release on or before Dec. 24
                if self.wage_type == 'monthly':
                    if self.payroll_schedule == '3_sm':
                        current_basic_pay *= 2
                    elif self.payroll_schedule == '2_w':
                        current_basic_pay *= 4
                else:
                    wd = self.contract_id.work_days
                    work_days_half_month = 0
                    if wd == '5wd':
                        if self.payroll_schedule == '3_sm':
                            work_days_half_month = (261 / 12) / 2
                        elif self.payroll_schedule == '2_w':
                            work_days_half_month = (261 / 12) / 4
                    else:
                        if self.payroll_schedule == '3_sm':
                            work_days_half_month = (313 / 12) / 2
                        elif self.payroll_schedule == '2_w':
                            work_days_half_month = (313 / 12) / 4
                    
                    current_basic_pay = work_days_half_month * self.daily_pay


            current_13th_amt = self._get_13th_mo_comp(current_basic_pay, {
                        'late': self.late_amount,
                        'ut': self.undertime_amount,
                        'ul': 0, #self.halfday_amount, # instead of Unpaid Leave/Absent Amount
                        'ot': self.overtime_amount,
                        'nd': self.night_diff_amount
                    })
            month_13th = current_13th_amt

            payroll_periods = self._get_payroll_periods_fiscal_year(self.payroll_period_id.fiscal_year_id.id).ids
            args = [
                ('employee_id', '=', self.employee_id.id),
                ('payroll_period_id', 'in', payroll_periods),
                ('state', '=', 'done'),
                ('credit_note', '=', False)
            ]
            slips = self.search(args)
            for s in slips:
                month_13th += self._get_13th_mo_comp(s.basic_pay, {
                        'late': s.late_amount,
                        'ut': s.undertime_amount,
                        'ul': 0, #s.halfday_amount, # instead of Unpaid Leave/Absent Amount
                        'ot': s.overtime_amount,
                        'nd': s.night_diff_amount
                    })

            self.slip_structure_ids = [(0, 0, {'adjustment_id': adj_13th_id, 'amount': month_13th, 'release_13th_pay': True})]

    def _get_payroll_periods_fiscal_year(self, fiscal_year_id):
        obj_pay_period = self.env['hr.payroll.period']
        return obj_pay_period.search([('fiscal_year_id', '=', fiscal_year_id)])

    def _extract_date(self, date):
        vals = {}
        y, m, d = str(date).split('-')
        vals['year'] = int(y)
        vals['month'] = int(m)
        vals['day'] = int(d)
        return vals

    @api.multi
    def _compute_ot(self):
        ot_list = []
        spec_holiday_ot = 0
        self.overtime_summary_ids = None

        obj_ot = self.env['hr.overtime']
        obj_ot_comp = self.env['hr.overtime.computation']
        args = [
            ('employee_id', '=', self.employee_id.id),
            ('payroll_period_id', '=', self.payroll_period_id.id),
            ('state', '=', 'approve')
        ]
        overtime = obj_ot.search(args)
        if overtime:
            for ot in overtime:
                for comp in ot.computation_ids:
                    if self.wage_type == 'daily':
                        if not ot.holiday:
                            ot_amount = comp.ot_hours * (obj_ot_comp.compute_rate(comp.computation_id.id, self.daily_pay))
                        else:
                            ot_amount = comp.ot_hours * (obj_ot_comp.compute_rate(comp.computation_id.id, self.daily_pay, holiday=True))
                    else:
                        ot_amount = comp.ot_hours * (obj_ot_comp.compute_rate(comp.computation_id.id, self.daily_pay, 'monthly'))
                    vals = {
                        'computation_id': comp.computation_id.id,
                        'ot_hours': comp.ot_hours,
                        'ot_amount': ot_amount
                    }
                    ot_list.append(vals)

                if ot.holiday:
                    for h in ot.holiday_ids:
                        if h.holiday_type == 'special':
                            spec_holiday_ot += 1

        result = {}
        for item in ot_list:
            res_item = result.get(item['computation_id'], None)
            if not res_item:
                res_item = {
                    'computation_id': item['computation_id'],
                    'ot_hours': item['ot_hours'],
                    'ot_amount': item['ot_amount']
                }
            else:
                res_item['ot_hours'] += item['ot_hours']
                res_item['ot_amount'] += item['ot_amount']
            result[item['computation_id']] = res_item

        for k, v in result.items():
            vals = {
                'computation_id': int(k),
                'ot_hours': v['ot_hours'],
                'ot_amount': v['ot_amount']
            }
            self.overtime_summary_ids = [(0, 0, vals)]

        ot_hrs = ot_amt = 0
        for ot in self.overtime_summary_ids:
            ot_hrs += ot.ot_hours
            ot_amt += ot.ot_amount

        self.overtime = ot_hrs
        self.overtime_amount = ot_amt
        self.spec_holiday_ot = spec_holiday_ot
        self.work_days += spec_holiday_ot

    def action_confirm(self):
        if self.payroll_schedule != self.contract_id.payroll_schedule:
            raise ValidationError(_('Payroll schedule must be the same with employee contract'))
        if self.state == 'draft':
            self.state = 'confirm'

    def action_cancel(self):
        if self.state == 'confirm':
            self.state = 'cancel'

    @api.multi
    def action_payslip_draft(self):
        if self.state in ('confirm', 'cancel'):
            self.state = 'draft'

    @api.multi
    def refund_sheet(self):
        for slip in self:
            vals = {
                'credit_note': True,
                'name': _('Refund: ') + slip.name,
                'basic_pay': -slip.basic_pay,
                'unpaid_leave_amount': -slip.unpaid_leave_amount if slip.unpaid_leave_amount > 0 else 0,
                'late_amount': -slip.late_amount if slip.late_amount > 0 else 0,
                'undertime_amount': -slip.undertime_amount if slip.undertime_amount > 0 else 0,
                'overtime_amount': -slip.overtime_amount if slip.overtime_amount > 0 else 0,
                'night_diff_amount': -slip.night_diff_amount if slip.night_diff_amount > 0 else 0,
                
                'hdmf_ee': -slip.hdmf_ee if slip.hdmf_ee > 0 else 0,
                'hdmf_er': -slip.hdmf_er if slip.hdmf_er > 0 else 0,
                'phic_ee': -slip.phic_ee if slip.phic_ee > 0 else 0,
                'phic_er': -slip.phic_er if slip.phic_er > 0 else 0,
                'sss_ee': -slip.sss_ee if slip.sss_ee > 0 else 0,
                'sss_ee_mpf': -slip.sss_ee_mpf if slip.sss_ee_mpf > 0 else 0,
                'sss_er': -slip.sss_er if slip.sss_er > 0 else 0,
                'sss_er_mpf': -slip.sss_er_mpf if slip.sss_er_mpf > 0 else 0,
                'total_premium': -slip.total_premium if slip.total_premium > 0 else 0,

                'gross_pay': -slip.gross_pay if slip.gross_pay > 0 else 0,
                'wtax': -slip.wtax if slip.wtax > 0 else 0,
                'other_earning': -slip.other_earning if slip.other_earning > 0 else 0,
                'other_deduction': -slip.other_deduction if slip.other_deduction > 0 else 0,
                'net_pay': -slip.net_pay if slip.net_pay > 0 else 0
            }
            copied_slip = slip.copy(vals)
            number = copied_slip.number or self.env['ir.sequence'].next_by_code('salary.slip')
            copied_slip.write({'number': number})

            if slip.move_id:
                move = slip.move_id.reverse_moves(date=date.today(), journal_id=slip.journal_id)
                copied_slip.write({'move_id': move[0] if move else None})
            copied_slip.write({'refund_slip_id': slip.id})
            copied_slip.with_context(without_compute_sheet=True).action_validate()
            slip.state = 'refund'

            if slip.convertible_leave:
                slip._refund_converted_leave()

    def _refund_converted_leave(self):
        for a in self.converted_leave_ids:
            a.leave_allocation_id.converted = False
            a.leave_allocation_id.payslip_id = None


class PayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    FILTER = [
        ('manager', 'Manager Only'),
        ('atm', 'ATM Employees Only'),
        ('non_atm', 'Non-ATM Employees Only')
    ]

    payroll_reg_id = fields.Many2one('hr.payslip.run', 'Payroll Register', required=True)
    employee_ids = fields.Many2many('hr.employee', 'hr_employee_group_rel', 'payslip_id', 'employee_id', 'Employees')
    employee_filter = fields.Selection(FILTER, string='Filter Options')

    @api.onchange('employee_filter')
    def onchange_employee_filter(self):
        obj_contract = self.env['hr.contract']
        domain = [('id', 'in', obj_contract._get_employees_with_this_pay_sched(self.payroll_reg_id.payroll_schedule))]
        if self.employee_filter == 'manager':
            domain.extend([('manager', '=', True)])
        elif self.employee_filter == 'atm':
            domain.extend([('salary_atm', '=', True)])
        elif self.employee_filter == 'non_atm':
            domain.extend([('salary_atm', '=', False)])
        return {'domain': {'employee_ids': domain}}

    @api.multi
    def compute_sheet(self):
        payslips = self.env['hr.payslip']
        obj_slip = self.env['hr.payslip']
        obj_pay_reg = self.env['hr.payslip.run']
        obj_contract = self.env['hr.contract']

        # active_id = self.env.context.get('active_id')
        # if not active_id:
        #     raise ValidationError(_('Payroll Register not found'))

        for obj in self:
            if not obj.employee_ids:
                raise ValidationError(_('You must select employee(s) to generate payslip(s)'))

            # pay_reg = obj_pay_reg.browse(active_id)
            pay_reg = obj.payroll_reg_id
            for emp in obj.employee_ids:
                # Check contract payroll schedule
                emp_contract = obj_contract.get_active_contract(employee=emp, contract_obj=True)
                if emp_contract.payroll_schedule == pay_reg.payroll_schedule:
                    vals = {
                        'payroll_period_id': pay_reg.payroll_period_id.id,
                        'payroll_schedule': pay_reg.payroll_schedule,
                        'journal_id': pay_reg.journal_id.id or None,
                        'cash_bank_account_id': pay_reg.cash_bank_account_id.id or None,
                        'employee_id': emp.id,
                        'payslip_run_id': pay_reg.id,
                        'date_from': pay_reg.payroll_period_id.period_fr,
                        'date_to': pay_reg.payroll_period_id.period_to,
                        'credit_note': pay_reg.credit_note,
                        'convertible_leave': pay_reg.convertible_leave,
                        'release_13th_pay': pay_reg.release_13th_pay,
                        'company_id': emp.company_id.id,
                        'journal_entry': pay_reg.journal_entry
                    }
                    payslips += obj_slip.create(vals)

            for slip in payslips:
                slip.onchange_employee(False)
                slip._compute_contract()
                slip._compute_work_days()
                slip._compute_premiums()
                slip._compute_leave()
                slip._compute_ot()
                slip._compute_canteen_loan()
                slip._compute_adjustment()

                slip._compute_convertible_leave()
                slip._compute_13th_pay()

                slip._compute_slip()
            return {'type': 'ir.actions.act_window_close'}


class OvertimeSummary(models.Model):
    _name = 'hr.overtime.summary'

    slip_id = fields.Many2one('hr.payslip', string='Payslip', ondelete='cascade')
    ot_hours = fields.Float(string='OT Hours')
    ot_amount = fields.Float(string='OT Amount', digits=dp.get_precision('Payroll'))


class LeaveSummary(models.Model):
    _name = 'hr.leave.summary'

    LEAVE_TYPE = [
        ('paid', 'Paid Leave'),
        ('unpaid', 'Unpaid Leave'),
        ('halfpaid', 'Half Paid Leave')
    ]

    slip_id = fields.Many2one('hr.payslip', string='Payslip', ondelete='cascade')
    holiday_status_id = fields.Many2one('hr.leave.type', 'Leave Request')
    leave_type = fields.Selection(LEAVE_TYPE)
    duration = fields.Float('Duration (Days)')
    amount = fields.Float(digits=dp.get_precision('Payroll'))


class PayslipStructure(models.Model):
    _name = 'hr.payslip.structure'

    slip_id = fields.Many2one('hr.payslip', ondelete='cascade')
    structure_line_id = fields.Many2one('hr.payroll.structure.line', ondelete='restrict')
    adjustment_id = fields.Many2one('hr.payroll.adjustment', string='Adjustment', required=True)
    adjustment_type = fields.Selection(related='adjustment_id.adjustment_type')
    adjustment_for = fields.Selection(related='adjustment_id.adjustment_for')
    computation = fields.Selection(related='adjustment_id.computation')
    rate = fields.Float(related='adjustment_id.rate')
    loan_id = fields.Many2one('hr.loan', string='Loans')
    canteen_id = fields.Many2one('hr.canteen', string='Canteen')
    amount = fields.Float(required=True, digits=dp.get_precision('Payroll'))
    payment_date = fields.Date(related='slip_id.date', string='Payment Date', store=True)
    ceiling_amount = fields.Float(help='Excess of the ceiling amount is subject to income tax. Zero amount means no limit', default=0)
    taxable_amount = fields.Float()
    convertible_leave = fields.Boolean()
    release_13th_pay = fields.Boolean('13th Month Pay')
    active = fields.Boolean(default=True)

    @api.onchange('adjustment_id', 'amount')
    def onchange_adjustment(self):
        ceiling_amt = self.adjustment_id.ceiling_amount
        if ceiling_amt > 0:
            if not self.structure_line_id:
                if ceiling_amt < self.amount:
                    self.ceiling_amount = ceiling_amt
                    self.taxable_amount = (self.amount - ceiling_amt)
        else:
            self.ceiling_amount = self.taxable_amount = 0


ADJUSTMENT_TYPE = [
    ('adjustment', 'Adjustment'),
    ('allowance', 'Allowance'),
    ('cashadvance', 'Cash Advance'),
    ('loan', 'Loan'),
    ('otherbenefit', 'Other Benefit'),
    ('otherearning', 'Other Earning'),
    ('otherdeduct', 'Other Deduction'),
    ('refund', 'Refund'),
    ('13th_mo', '13th Month Pay'),
    ('14th_mo', '14th Month Pay')
]

class PayrollAdjustment(models.Model):
    _name = 'hr.payroll.adjustment'
    _order = 'sequence, name'
    _description = 'Payroll Adjustment/Structure'

    ADJUSTMENT_FOR = [
        ('basic', 'Basic Salary'),
        ('lwp', 'Leave With Pay'),
        ('lwop', 'Leave Without Pay'),
        ('late', 'Late'),
        ('undertime', 'Undertime'),
        ('cola', 'COLA'),
        ('ot', 'Overtime'),
        ('nd', 'Night Differential'),
        ('hdmf_prem', 'HDMF Premium'),
        ('phic_prem', 'PHIC Premium'),
        ('sss_prem', 'SSS Premium'),
        ('wtax', 'Withholding Tax'),
        ('earn', 'Other Earnings'),
        ('deduct', 'Other Deductions')
    ]

    COMPUTATION = [
        ('fix', 'Fixed'),
        ('pct', 'Percentage')
    ]

    PRODUCT_TYPE = [
        ('hdmf_loan', 'HDMF Loan'),
        ('phic_loan', 'PHIC Loan'),
        ('sss_loan', 'SSS Loan'),
    ]

    MONTH_13TH = [
        (1, 'Basic Pay / 12 Months'),
        (2, '(Basic Pay - (Late + Undertime + Unpaid Leave/Absence)) / 12 Months'),
        (3, '((Basic Pay + Overtime + Night. Diff.) - (Late + Undertime + Unpaid Leave/Absence)) / 12 Months'),
    ]

    name = fields.Char(required=True)
    adjustment_type = fields.Selection(ADJUSTMENT_TYPE, required=True)
    adjustment_for = fields.Selection(ADJUSTMENT_FOR)
    computation = fields.Selection(COMPUTATION, required=True, default='fix')
    rate = fields.Float(string='Percentage (%)')
    sequence = fields.Integer()
    ga_other_assets_account_id = fields.Many2one('account.account', string='Other Assets Account')
    ga_liability_account_id = fields.Many2one('account.account', string='Liability Account')
    ga_extra_liability_account_id = fields.Many2one('account.account', string='Payroll Account')
    ho_other_assets_account_id = fields.Many2one('account.account', string='Other Assets Account')
    ho_liability_account_id = fields.Many2one('account.account', string='Liability Account')
    ho_extra_liability_account_id = fields.Many2one('account.account', string='Payroll Account')
    journal_id = fields.Many2one('account.journal', string='Journal')
    product_type = fields.Selection(PRODUCT_TYPE, string='Type')
    rice_allowance_ids = fields.One2many('hr.rice.allowance.computation', 'adjustment_id')
    rice_allowance = fields.Boolean()
    ceiling_amount = fields.Float(help='Excess of the ceiling amount is subject to income tax. Zero amount means no limit', default=0)
    month13th_comp = fields.Selection(MONTH_13TH, string='Computation', default=2)


class PayrollStructureLine(models.Model):
    _name = 'hr.payroll.structure.line'
    _order = 'date desc'
    _rec_name = 'adjustment_id'

    STATE = [
        ('open', 'Open/Running'),
        ('done', 'Paused/Done')
    ]

    date = fields.Date(required=True, default=lambda *d: date.today())
    contract_id = fields.Many2one('hr.contract', string='Contract', ondelete='restrict')
    employee_id = fields.Many2one(related='contract_id.employee_id', model='hr.employee', string='Employee', store=True)
    adjustment_id = fields.Many2one('hr.payroll.adjustment', string='Adjustment', required=True)
    adjustment_type = fields.Selection(related='adjustment_id.adjustment_type', store=True)
    adjustment_for = fields.Selection(related='adjustment_id.adjustment_for', store=True)
    computation = fields.Selection(related='adjustment_id.computation', store=True)
    rate = fields.Float(related='adjustment_id.rate', store=True)
    period_type = fields.Selection(PERIOD_TYPE, required=True, default='1st_2nd', help='The period to which this adjustment will be process')
    loan_id = fields.Many2one('hr.loan', string='Loans')
    amount = fields.Float(required=True, digits=dp.get_precision('Payroll'), help='The amount to be process base on Period Type')
    state = fields.Selection(STATE, default='open')
    slip_structure_ids = fields.One2many('hr.payslip.structure', 'structure_line_id')

    # @api.multi
    # @api.constrains('contract_id', 'loan_id')
    # def _check_duplicate_loan(self):
    #     for obj in self:
    #         args = [
    #             ('contract_id', '=', obj.contract_id.id),
    #             ('adjustment_id', '=', obj.adjustment_id.id),
    #             ('state', '=', 'open')
    #         ]
    #         if len(obj.search(args)) > 1:
    #             raise ValidationError(_('%s already exists' % (obj.adjustment_id.name)))

    @api.onchange('adjustment_id', 'period_type')
    def onchange_adjustment(self):
        # Compute rice allowance
        adj_id = self.env.ref('ph_payroll_computation.adj_rice_allowance').id
        if self.adjustment_id.id == adj_id:
            yis = self.contract_id.employee_id.yis_months
            if yis > 0:
                yis *= 12 # convert to number of months
                for a in self.adjustment_id.rice_allowance_ids:
                    if yis >= a.month_fr and yis <= a.month_to:
                        if self.period_type == '1st_2nd':
                            self.amount = a.amount / 2
                        else:
                            self.amount = a.amount
        else:
            self.amount = 0

    @api.onchange('loan_id', 'period_type')
    def onchange_loan(self):
        if self.loan_id:
            self.adjustment_id = self.loan_id.adjustment_id.id
            if self.period_type == '1st_2nd':
                self.amount = self.loan_id.monthly_payment / 2.0
            else:
                self.amount = self.loan_id.monthly_payment

    def mark_done(self):
        self.state = 'done'

    def mark_open(self):
        self.state = 'open'


class EmployeeContract(models.Model):
    _inherit = 'hr.contract'

    structure_ids = fields.One2many('hr.payroll.structure.line', 'contract_id', string='Salary Structure', copy=True)


class DayOffCalendar(models.Model):
    _inherit = 'hr.dayoff.calendar'

    @api.multi
    @api.depends('day_off_date')
    def _compute_day_off(self):
        res = super(DayOffCalendar, self)._compute_day_off()
        for obj in self:
            pay_period = self.env['hr.payroll.period']._get_payroll_period(obj.contract_id.payroll_schedule, obj.day_off_date)
            obj.payroll_period_id = pay_period.id if pay_period else None

    payroll_period_id = fields.Many2one('hr.payroll.period', compute=_compute_day_off, string='Payroll Period', store=True)

    @api.constrains('employee_id', 'payroll_period_id')
    def _check_day_off(self):
        no_of_dayoff = 0
        if self.employee_id.contract_ids:
            active_contract = self.employee_id.contract_ids.filtered(lambda c: c.state == 'open')
            no_of_dayoff = active_contract.no_of_dayoff

        if not self.payroll_period_id:
            raise ValidationError(_('No payroll period found for this date'))

        args = [
            ('employee_id', '=', self.employee_id.id),
            ('payroll_period_id', '=', self.payroll_period_id.id)
        ]
        if len(self.search(args)) > no_of_dayoff:
            raise ValidationError(_("'%s' is only allowed %s day-off within the payroll period. Go to employee contract to change the setting" % (
                self.employee_id.name, no_of_dayoff)))

    @api.constrains('employee_id', 'day_off_date')
    def _check_day_off_date(self):
        args = [
            ('employee_id', '=', self.employee_id.id),
            ('day_off_date', '=', self.day_off_date)
        ]
        if len(self.search(args)) > 1:
            raise ValidationError(_("'%s' already has day-off set for this date" % (
                self.employee_id.name)))

    def _check_valid_work_sched(self, contract_id, day_off_date):
        obj_contract = self.env['hr.contract']
        contract = obj_contract.browse(contract_id)
        if not contract.work_shift_fix:
            query = '''
                SELECT resource_calendar_id
                FROM hr_contract_work_schedule
                WHERE contract_id = %s
                    AND %s BETWEEN date_fr AND date_to
                    AND state = 'open'
            '''
            self.env.cr.execute(query, [contract_id, day_off_date])
            if not self.env.cr.dictfetchall():
                raise ValidationError(_('No valid work schedule found for contract: %s' % (contract.name)))

    @api.model
    def create(self, vals):
        res = super(DayOffCalendar, self).create(vals)
        self._check_valid_work_sched(res.contract_id.id, res.day_off_date)
        return res

    @api.multi
    def write(self, vals):
        res = super(DayOffCalendar, self).write(vals)
        for obj in self:
            if 'day_off_date' in vals:
                obj._check_valid_work_sched(obj.contract_id.id, obj.day_off_date)

            ctx = dict(obj.env.context)
            if '__contexts' in ctx and ctx['__contexts']:
                if 'from_ui' in ctx['__contexts'][1]:
                    if ctx['__contexts'][1]['from_ui']:
                        pay_period = self.env['hr.payroll.period']._get_payroll_period(vals['payroll_schedule'], vals['day_off_date'])
                        if pay_period:
                            vals['payroll_period_id'] = pay_period.id
                        else:
                            raise ValidationError(_('No payroll period found for this date'))
        return res


class Loan(models.Model):
    _inherit = 'hr.loan'

    adjustment_id = fields.Many2one('hr.payroll.adjustment', string='Loan Type')
    period_type = fields.Selection(PERIOD_TYPE, required=True, default='1st_2nd', help='The period to which this adjustment will be process')

    @api.onchange('adjustment_id')
    def onchange_adjustment(self):
        adj = self.adjustment_id
        self.other_assets_account_id = None
        self.liability_account_id = None
        self.journal_id = None

        self.other_assets_account_id = adj.ga_other_assets_account_id.id if adj.ga_other_assets_account_id else None
        self.liability_account_id = adj.ga_liability_account_id.id if adj.ga_liability_account_id else None

        self.journal_id = adj.journal_id.id if adj.journal_id else None


class Canteen(models.Model):
    _inherit = 'hr.canteen'

    payroll_period_id = fields.Many2one('hr.payroll.period', string='Payment Period')

    @api.onchange('date')
    def onchange_date(self):
        pp = self.env['hr.payroll.period']._get_payroll_period(self.contract_id.payroll_schedule, self.date)
        self.payroll_period_id = pp.id if pp else None


class Department(models.Model):
    _inherit = 'hr.department'

    salary_wage_account_id = fields.Many2one('account.account', string='Account')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    payroll_cash_bank_account_id = fields.Many2one('account.account', string='Cash in Bank Account')
    taxable_ot = fields.Boolean('Taxable Overtime', default=True)
    company_bank_account_no = fields.Char('Bank Account No.')
    post_slip_journal_entries = fields.Boolean('Post to Journal')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            payroll_cash_bank_account_id=int(self.env['ir.config_parameter'].sudo().get_param(
                'payslip.payroll_cash_bank_account_id')),
            taxable_ot=bool(self.env['ir.config_parameter'].sudo().get_param(
                'payslip.taxable_ot')),
            company_bank_account_no=str(self.env['ir.config_parameter'].sudo().get_param(
                'payslip.company_bank_account_no')),
            post_slip_journal_entries=bool(self.env['ir.config_parameter'].sudo().get_param(
                'payslip.post_slip_journal_entries')),
            )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'payslip.payroll_cash_bank_account_id', self.payroll_cash_bank_account_id.id)
        self.env['ir.config_parameter'].sudo().set_param(
            'payslip.taxable_ot', self.taxable_ot)
        self.env['ir.config_parameter'].sudo().set_param(
            'payslip.company_bank_account_no', self.company_bank_account_no)
        self.env['ir.config_parameter'].sudo().set_param(
            'payslip.post_slip_journal_entries', self.post_slip_journal_entries)


class RiceAllowanceComputation(models.Model):
    _name = 'hr.rice.allowance.computation'
    _order = 'month_fr'

    adjustment_id = fields.Many2one('hr.payroll.adjustment', string='Adjustment/Structure', ondelete='cascade')
    month_fr = fields.Integer(string='Month From', required=True)
    month_to = fields.Integer(string='Month To', required=True)
    amount = fields.Float(required=True)
    notes = fields.Text()


class LeaveConvert(models.Model):
    _name = 'hr.leave.convert'

    payslip_id = fields.Many2one('hr.payslip', ondelete='cascade')
    leave_allocation_id = fields.Many2one('hr.leave.allocation', string='Leave Allocation')
    holiday_status_id = fields.Many2one(related='leave_allocation_id.holiday_status_id', model='hr.leave.type')
    fiscal_year_id = fields.Many2one('account.fiscal.year')
    total_allocation = fields.Float()
    convertible_leave = fields.Float()
    leave_count = fields.Float('Leaves Taken')
    leave_balance = fields.Float('Remaining Leaves')
    converted_days = fields.Float()
    amount = fields.Float()


class PayslipReportView(models.Model):
    _name = 'hr.payslip.report.view'
    _auto = False

    name = fields.Many2one('hr.employee', string='Employee')
    payroll_period_id = fields.Many2one('hr.payroll.period', string='Payroll Period')
    date_from = fields.Date(string='Payroll From')
    date_to = fields.Date(string='Payroll To')
    department_id = fields.Many2one('hr.department', string='Department')
    job_id = fields.Many2one('hr.job', string='Job Title')
    state = fields.Selection(PAYSLIP_STATE)

    basic_pay = fields.Float()
    cola_amount = fields.Float()
    unpaid_leave_amount = fields.Float(string='Up. Leave/Absent Amt.')
    late_amount = fields.Float()
    undertime_amount = fields.Float()
    overtime_amount = fields.Float()
    night_diff_amount = fields.Float()

    hdmf_ee = fields.Float(string='HDMF (EE)')
    hdmf_er = fields.Float(string='HDMF (ER)')
    phic_ee = fields.Float(string='PHIC (EE)')
    phic_er = fields.Float(string='PHIC (ER)')
    sss_ee = fields.Float(string='SSS (EE)')
    sss_ee_mpf = fields.Float(string='SSS MPF (EE)')
    sss_er = fields.Float(string='SSS (ER)')
    sss_er_mpf = fields.Float(string='SSS MPF (ER)')

    gross_pay = fields.Float()
    wtax = fields.Float(string='W-Tax')
    other_earning = fields.Float()
    other_deduction = fields.Float()
    net_pay = fields.Float()
    month_13th = fields.Float(string='13th Month')

    salary_atm = fields.Boolean('Salary Through ATM')

    def _select(self):
        select_str = '''
            min(slip.id) AS id, emp.id AS name, pp.id AS payroll_period_id, slip.date_from, slip.date_to, dept.id AS department_id, job.id AS job_id, slip.state,
            slip.basic_pay, slip.cola_amount, COALESCE(slip.unpaid_leave_amount, 0) AS unpaid_leave_amount, slip.late_amount, slip.undertime_amount, slip.overtime_amount, slip.night_diff_amount,
            slip.hdmf_ee, slip.hdmf_er, slip.phic_ee, slip.phic_er, slip.sss_ee, slip.sss_ee_mpf, slip.sss_er, slip.sss_er_mpf,
            slip.gross_pay, slip.wtax, slip.other_earning, slip.other_deduction, slip.net_pay, slip.month_13th, emp.salary_atm
            '''
        return select_str

    def _from(self):
        from_str = '''
            hr_payslip AS slip
            INNER JOIN hr_employee AS emp ON emp.id = slip.employee_id
            INNER JOIN hr_payroll_period AS pp ON pp.id = slip.payroll_period_id
            LEFT JOIN hr_department AS dept ON dept.id = emp.department_id
            LEFT JOIN hr_job AS job ON job.id = emp.job_id
            LEFT JOIN hr_payslip_structure AS ps ON ps.slip_id = slip.id
            LEFT JOIN hr_payroll_adjustment AS adj ON adj.id = ps.adjustment_id
            '''
        return from_str

    def _where(self):
        where_str = '''
            WHERE slip.state in ('confirm', 'done') AND NOT slip.credit_note
            '''
        return where_str

    def _group_by(self):
        group_by_str = '''
            GROUP BY emp.id, pp.id, slip.date_from, slip.date_to, dept.id, job.id, slip.state,
            slip.basic_pay, slip.cola_amount, slip.unpaid_leave_amount, slip.late_amount, slip.undertime_amount, slip.overtime_amount, slip.night_diff_amount,
            slip.hdmf_ee, slip.hdmf_er, slip.phic_ee, slip.phic_er, slip.sss_ee, slip.sss_ee_mpf, slip.sss_er, slip.sss_er_mpf,
            slip.gross_pay, slip.wtax, slip.other_earning, slip.other_deduction, slip.net_pay, slip.month_13th, emp.salary_atm
        '''
        return group_by_str

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''CREATE or REPLACE VIEW %s AS (
                SELECT %s FROM %s %s %s
            )''' % (self._table, self._select(), self._from(), self._where(), self._group_by()))


class PayslipReportDetailedView(models.Model):
    _name = 'hr.payslip.report.detailed.view'
    _inherit = 'hr.payslip.report.view'

    adjustment_type = fields.Selection(ADJUSTMENT_TYPE)
    adj_name = fields.Char(string='Adjustment Name')
    adj_amount = fields.Float(string='Adjustment Amount')
    earn_deduct = fields.Char(string='Earn/Deduct')

    def _sub_select(self):
        sub_select_str = '''
            sub.id, sub.name, sub.payroll_period_id, sub.date_from, sub.date_to, sub.department_id, sub.job_id, sub.state,
            COALESCE((sub.basic_pay / NULLIF(sub.cnt, 0)), sub.basic_pay) AS basic_pay,
            COALESCE((sub.cola_amount / NULLIF(sub.cnt, 0)), sub.cola_amount) AS cola_amount,
            COALESCE((sub.unpaid_leave_amount / NULLIF(sub.cnt, 0)), sub.unpaid_leave_amount) AS unpaid_leave_amount,
            COALESCE((sub.late_amount / NULLIF(sub.cnt, 0)), sub.late_amount) AS late_amount,
            COALESCE((sub.undertime_amount / NULLIF(sub.cnt, 0)), sub.undertime_amount) AS undertime_amount, 
            COALESCE((sub.overtime_amount / NULLIF(sub.cnt, 0)), sub.overtime_amount) AS overtime_amount,
            COALESCE((sub.night_diff_amount / NULLIF(sub.cnt, 0)), sub.night_diff_amount) AS night_diff_amount,
            COALESCE((sub.hdmf_ee / NULLIF(sub.cnt, 0)), sub.hdmf_ee) AS hdmf_ee,
            COALESCE((sub.hdmf_er / NULLIF(sub.cnt, 0)), sub.hdmf_er) AS hdmf_er,
            COALESCE((sub.phic_ee / NULLIF(sub.cnt, 0)), sub.phic_ee) AS phic_ee,
            COALESCE((sub.phic_er / NULLIF(sub.cnt, 0)), sub.phic_er) AS phic_er,
            COALESCE((sub.sss_ee / NULLIF(sub.cnt, 0)), sub.sss_ee) AS sss_ee,
            COALESCE((sub.sss_ee_mpf / NULLIF(sub.cnt, 0)), sub.sss_ee_mpf) AS sss_ee_mpf,
            COALESCE((sub.sss_er / NULLIF(sub.cnt, 0)), sub.sss_er) AS sss_er,
            COALESCE((sub.sss_er_mpf / NULLIF(sub.cnt, 0)), sub.sss_er_mpf) AS sss_er_mpf,
            COALESCE((sub.gross_pay / NULLIF(sub.cnt, 0)), sub.gross_pay) AS gross_pay,
            COALESCE((sub.wtax / NULLIF(sub.cnt, 0)), sub.wtax) AS wtax,
            COALESCE((sub.other_earning / NULLIF(sub.cnt, 0)), sub.other_earning) AS other_earning,
            COALESCE((sub.other_deduction/ NULLIF(sub.cnt, 0)), sub.other_deduction) AS other_deduction,
            COALESCE((sub.net_pay / NULLIF(sub.cnt, 0)), sub.net_pay) AS net_pay,
            COALESCE((sub.month_13th / NULLIF(sub.cnt, 0)), sub.month_13th) AS month_13th,
            sub.salary_atm, sub.adjustment_type, sub.adj_name, sub.adj_amount, sub.earn_deduct
            '''
        return sub_select_str

    def _select(self):
        select_str = '''
            min(slip.id) AS id, emp.id AS name, pp.id AS payroll_period_id, slip.date_from, slip.date_to, dept.id AS department_id, job.id AS job_id, slip.state,
            slip.basic_pay, slip.cola_amount, COALESCE(slip.unpaid_leave_amount, 0) AS unpaid_leave_amount, slip.late_amount, slip.undertime_amount, slip.overtime_amount, slip.night_diff_amount,
            slip.hdmf_ee, slip.hdmf_er, slip.phic_ee, slip.phic_er, slip.sss_ee, slip.sss_ee_mpf, slip.sss_er, slip.sss_er_mpf,
            slip.gross_pay, slip.wtax, slip.other_earning, slip.other_deduction, slip.net_pay, slip.month_13th, emp.salary_atm,
            adj.adjustment_type, adj.name AS adj_name, ps.amount AS adj_amount,
            CASE WHEN adj.adjustment_type IN ('allowance', 'otherbenefit', 'otherearning', 'refund', '13th_mo', '14th_mo') THEN 'EARN' ELSE 'DEDUCT' END AS earn_deduct,
            COALESCE((SELECT COUNT(id) FROM hr_payslip_structure WHERE slip_id = slip.id),1) AS cnt
            '''
        return select_str

    def _from(self):
        from_str = '''
            hr_payslip AS slip
            INNER JOIN hr_employee AS emp ON emp.id = slip.employee_id
            INNER JOIN hr_payroll_period AS pp ON pp.id = slip.payroll_period_id
            LEFT JOIN hr_department AS dept ON dept.id = emp.department_id
            LEFT JOIN hr_job AS job ON job.id = emp.job_id
            LEFT JOIN hr_payslip_structure AS ps ON ps.slip_id = slip.id
            LEFT JOIN hr_payroll_adjustment AS adj ON adj.id = ps.adjustment_id
            '''
        return from_str

    def _where(self):
        where_str = '''
            WHERE slip.state in ('confirm', 'done') AND NOT slip.credit_note
            '''
        return where_str

    def _group_by(self):
        group_by_str = '''
            slip.id, emp.id, pp.id, slip.date_from, slip.date_to, dept.id, job.id, slip.state,
            slip.basic_pay, slip.cola_amount, slip.unpaid_leave_amount, slip.late_amount, slip.undertime_amount, slip.overtime_amount, slip.night_diff_amount,
            slip.hdmf_ee, slip.hdmf_er, slip.phic_ee, slip.phic_er, slip.sss_ee, slip.sss_ee_mpf, slip.sss_er, slip.sss_er_mpf,
            slip.gross_pay, slip.wtax, slip.other_earning, slip.other_deduction, slip.net_pay, slip.month_13th, emp.salary_atm,
            adj.adjustment_type, adj.name, ps.amount, earn_deduct
        '''
        return group_by_str

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''CREATE or REPLACE VIEW %s AS (
                SELECT %s
                FROM (SELECT %s FROM %s %s GROUP BY %s) AS sub
            )''' % (self._table, self._sub_select(), self._select(), self._from(), self._where(), self._group_by()))
