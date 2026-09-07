from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, datetime


DOW = [
    ('0', 'Monday'),
    ('1', 'Tuesday'),
    ('2', 'Wednesday'),
    ('3', 'Thursday'),
    ('4', 'Friday'),
    ('5', 'Saturday'),
    ('6', 'Sunday')
]

class EmployeeContract(models.Model):
    _inherit = 'hr.contract'

    WAGE_TYPE = [
        ('daily', 'Daily Paid'),
        ('monthly', 'Monthly Paid')
    ]

    CLASSIFICATION = [
        ('rank_file', 'Rank and File'),
        ('supervisor', 'Supervisory'),
        ('manager', 'Managerial')
    ]

    PAYROLL_SCHEDULE = [
        ('1_d', 'Daily'),
        ('2_w', 'Weekly'),
        ('3_sm', 'Semi-Monthly'),
        ('4_m', 'Monthly')
    ]

    WORK_DAYS = [
        ('5wd', '5 working days or 261 days in a year'),
        ('6wd', '6 working days or 313 days in a year')
    ]

    @api.multi
    def _check_work_sched(self):
        for obj in self:
            if not obj.work_shift_fix and len(obj.work_schedule_ids) == 0:
                obj.work_shift_fix = True

    @api.model
    def create(self, vals):
        res = super(EmployeeContract, self).create(vals)
        res._check_work_sched()
        return res

    @api.multi
    def write(self, vals):
        res = super(EmployeeContract, self).write(vals)
        self._check_work_sched()
        return res

    @api.multi
    @api.returns('self', lambda value: value.id)
    def copy(self, default={}):
        ctx = dict(self._context)
        if not 'new_contract' in ctx:
            raise ValidationError(_('You cannot duplicate a contract'))
        return super(EmployeeContract, self).copy(default=default)

    @api.model
    def _get_work_schedule(self):
        return self.env.ref('resource.resource_calendar_std', None).id

    @api.model
    def _get_salary_journal(self):
        obj_payslip_run = self.env['hr.payslip.run']
        return obj_payslip_run._get_salary_journal()

    name = fields.Char('Contract Reference', required=False)
    type_id = fields.Many2one('hr.contract.type', string="Contract Type", required=True,
        default=lambda self: self.env['hr.contract.type'].search([], limit=1))
    resource_calendar_id = fields.Many2one('resource.calendar', 'Work Schedule', default=_get_work_schedule, required=False)
    journal_id = fields.Many2one('account.journal', 'Salary Journal', default=_get_salary_journal)
    wage_type = fields.Selection(WAGE_TYPE, default='daily', required=True)
    factor_days = fields.Integer(default=365)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    classification = fields.Selection(CLASSIFICATION, default='rank_file')
    payroll_schedule = fields.Selection(PAYROLL_SCHEDULE, default='3_sm')
    work_shift_fix = fields.Boolean(string='Fix Work Schedule', default=True)
    hdmf = fields.Boolean(string='HDMF')
    hdmf_amount = fields.Float(string='Amount')
    phic = fields.Boolean(string='PHIC')
    phic_amount = fields.Float(string='Amount')
    sss = fields.Boolean(string='SSS')
    sss_amount = fields.Float(string='Amount')
    work_days = fields.Selection(WORK_DAYS, 'Working Days a Week')
    daily_pay = fields.Monetary(required=True, default=0.0)
    work_schedule_ids = fields.One2many('hr.contract.work.schedule', 'contract_id', copy=True)
    no_of_dayoff = fields.Integer(string='No. of Days', default=2)
    has_attendance = fields.Boolean()
    has_night_diff = fields.Boolean('Has Night Diff.')
    has_holiday = fields.Boolean()
    compute_late = fields.Boolean()
    compute_undertime = fields.Boolean()
    paid_reg_holiday = fields.Boolean(string='Paid Reg. Holiday')
    premiums_excluded = fields.Boolean(string='Exclude in Gross Taxable', help='Total Employee (EE) premiums is excluded in Gross Taxable')

    wage_rate_id = fields.Many2one('hr.wage.rate', 'Wage Rate')
    cola_amount = fields.Monetary('COLA', help='Cost of Living Allowance')
    total_daily_pay = fields.Monetary(compute='_compute_total_daily_pay', store=True)

    @api.onchange('wage_rate_id')
    def onchange_wage_rate(self):
        if self.wage_rate_id:
            self.daily_pay = self.wage_rate_id.basic_wage
            self.cola_amount = self.wage_rate_id.cola

    @api.multi
    @api.depends('daily_pay', 'cola_amount')
    def _compute_total_daily_pay(self):
        for obj in self:
            if obj.wage_type == 'daily':
                obj.total_daily_pay = obj.daily_pay + obj.cola_amount

    @api.onchange('wage_type')
    def onchange_wage_type(self):
        if self.wage_type == 'daily':
            self.has_attendance = True
            self.has_night_diff = True
            self.has_holiday= True
            self.compute_late = True
            self.compute_undertime = True
            self.paid_reg_holiday = True
            self.work_days = '6wd'
        else:
            self.has_attendance = False
            self.has_night_diff = True
            self.has_holiday= False
            self.compute_late = False
            self.compute_undertime = False
            self.paid_reg_holiday = False
            self.work_days = None
            self.cola_amount = 0
            self.wage_rate_id = None

        self._compute_total_daily_pay()
        self.compute_daily_monthly_rate()

    @api.onchange('work_days', 'wage', 'daily_pay', 'cola_amount', 'factor_days')
    def compute_daily_monthly_rate(self):
        if self.wage_type == 'monthly':
            self.daily_pay = (self.wage * 12) / self.factor_days
        else:
            if self.work_days == '5wd':
                self.wage = (self.total_daily_pay * 261) / 12
            else:
                self.wage = (self.total_daily_pay * 313) / 12

    @api.onchange('employee_id', 'date_start', 'job_id')
    def onchange_contract_reference(self):
        ln = job = ds = ''
        if self.employee_id:
            ln = (self.employee_id.last_name).strip()
        if self.job_id:
            job = (self.job_id.name[:3]).upper().strip()
        if self.date_start:
            ds = (self.date_start).strftime('%m%d%y')

        self.name = '%s%s%s' % (ln, job, ds)

    @api.onchange('work_shift_fix')
    def onchange_work_shift_fix(self):
        if not self.work_shift_fix:
            self.resource_calendar_id = None
        else:
            self.resource_calendar_id = self._get_work_schedule()

    @api.onchange('hdmf', 'phic', 'sss')
    def onchange_premium(self):
        if not self.hdmf:
            self.hdmf_amount = 0
        if not self.phic:
            self.phic_amount = 0
        if not self.sss:
            self.sss_amount = 0

    def get_active_contract(self, employee, show=True, contract_obj=False):
        if employee:
            args = [
                ('employee_id', '=', employee.id),
                ('state', '=', 'open')
            ]
            contract = self.search(args, limit=1)
            if not contract:
                if show:
                    raise ValidationError(_('%s has no active contract' % (employee.name)))
                else:
                    return None
            else:
                if not contract_obj:
                    return contract.id
                else:
                    return contract

    @api.constrains('employee_id', 'state')
    def _check_contract(self):
        args = [('employee_id', '=', self.employee_id.id), ('state', '=', 'open')]
        if len(self.search(args)) > 1:
            raise ValidationError(_('This employee already has active running contract'))

    @api.multi
    def unlink(self):
        for contract in self:
            if contract.state != 'draft':
                raise ValidationError('You cannot delete a contract which is not in draft state')
        return super(EmployeeContract, self).unlink()

    def action_open(self):
        if self.department_id: self.employee_id.department_id = self.department_id.id
        if self.job_id: self.employee_id.job_id = self.job_id.id

        self.state = 'open'

    def action_pending(self):
        self.state = 'pending'

    def action_close(self):
        self.state = 'close'

    def action_cancel(self):
        self.state = 'cancel'

    def action_draft(self):
        self.state = 'draft'

    @api.multi
    def create_new_contract(self):
        for obj in self:
            default = {
                'create_date': datetime.now(),
                'date_start': date.today(),
                'date_end': None,
                'structure_ids': [(6, 0, obj.structure_ids.filtered(lambda s: s.state == 'open').ids)],
                'work_schedule_ids': [(6, 0, obj.work_schedule_ids.filtered(lambda s: s.state == 'open').ids)]
            }
            new_contract = obj.with_context(new_contract=True).copy(default=default)
            new_contract.onchange_contract_reference()

            obj.date_end = date.today()
            obj.state = 'close'

            return {
                'name': 'Contract',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'hr.contract',
                'target': 'current',
                'res_id': new_contract.id,
                'context': {'form_view_initial_mode': 'edit'}
            }

    def _get_employment_contract(self, current_contract=False):
        data = {
            'date_start': '',
            'date_end': 'Present',
            'current_position': '',
            'day': '',
            'month': '',
            'year': ''

        }
        for obj in self:
            if not current_contract:
                contracts = obj.search([('employee_id', '=', obj.employee_id.id)], order='date_start')
                if contracts:
                    fl_contracts = [contracts[i] for i in (0, -1)]
                    data['date_start'] = (fl_contracts[0].date_start).strftime('%m/%d/%Y')
                    date_end = fl_contracts[1].date_end
                    data['current_position'] = fl_contracts[1].job_id.name if fl_contracts[1].job_id else '-'
                    if date_end:
                        data['date_end'] = (date_end).strftime('%m/%d/%Y')
            else:
                data['date_start'] = (obj.date_start).strftime('%m/%d/%Y')
                data['current_position'] = obj.job_id.name if obj.job_id else '-'
                if obj.date_end:
                    data['date_end'] = (obj.date_end).strftime('%m/%d/%Y')

        ordinal = lambda n: "".join([str(n), ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)] if not 11 <= n <= 13 else "th"])
        data['day'] = ordinal(int(date.today().strftime('%d')))
        data['month'] = date.today().strftime('%B')
        data['year'] = date.today().strftime('%Y')
        return data

    def _get_employees_with_this_pay_sched(self, payroll_schedule):
        args = [
            ('payroll_schedule', '=', payroll_schedule),
            ('state', '=', 'open')
        ]
        contracts = self.search(args)
        return [c.employee_id.id for c in contracts]


WORK_SCHED_STATE = [
    ('draft', 'Draft'),
    ('open', 'Running'),
    ('close', 'Closed')
]

class WorkShiftSchedule(models.Model):
    _name = 'hr.contract.work.schedule'
    _description = 'Flexible Work Schedule'
    _order = 'date_fr desc'

    @api.multi
    def name_get(self):
        res = super(WorkShiftSchedule, self).name_get()
        for obj in self:
            period_fr = fields.Date.to_string(obj.date_fr)
            period_to = fields.Date.to_string(obj.date_to)
            name = "%s - [%s - %s]" % (obj.resource_calendar_id.name, period_fr, period_to)
            res.append((obj.id, name))
        return res

    @api.multi
    def unlink(self):
        for sched in self:
            if sched.state != 'draft':
                raise ValidationError('You cannot delete a work schedule which is not in draft state')
        return super(WorkShiftSchedule, self).unlink()

    contract_id = fields.Many2one('hr.contract', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', related='contract_id.employee_id', store=True)
    department_id = fields.Many2one('hr.department', related='contract_id.department_id', store=True)
    resource_calendar_id = fields.Many2one('resource.calendar', 'Work Schedule', required=True)
    date_fr = fields.Date(string='Valid From', required=True)
    date_to = fields.Date(string='Valid To', required=True)
    state = fields.Selection(WORK_SCHED_STATE, default='draft')
    all_day = fields.Boolean(default=True)
    work_sched_line_ids = fields.One2many('hr.contract.work.schedule.line', 'work_sched_id')

    @api.onchange('employee_id')
    def onchange_employee(self):
        obj_contract = self.env['hr.contract']
        contract_id = None
        if self.employee_id:
            contract_id = obj_contract.get_active_contract(self.employee_id, False)
            if not contract_id:
                raise ValidationError(_('%s has no active contract' % (self.employee_id.name)))
            self.contract_id = contract_id

    @api.multi
    def _check_overlapping(self):
        for obj in self:
            date_fr = fields.Date.to_string(obj.date_fr)
            date_to = fields.Date.to_string(obj.date_to)

            clause_1 = ['&', ('date_to', '<=', date_to), ('date_to', '>=', date_fr)]
            clause_2 = ['&', ('date_fr', '<=', date_to), ('date_fr', '>=', date_fr)]
            clause_3 = ['&', ('date_fr', '<=', date_fr), '|', ('date_to', '=', False), ('date_to', '>=', date_to)]
            clause_final = [('contract_id', '=', obj.contract_id.id), ('state', '=', 'open'), '|', '|'] + clause_1 + clause_2 + clause_3
            
            work_scheds = obj.search(clause_final)
            if work_scheds:
                raise ValidationError(_("New work schedule for '%s' overlaps with his/her running schedule '%s - %s'" % (
                    obj.employee_id.name, (work_scheds[0].date_fr).strftime('%m/%d/%Y'), (work_scheds[0].date_to).strftime('%m/%d/%Y'))))

    @api.multi
    def action_run(self):
        for obj in self:
            obj._check_overlapping()
            obj.state = 'open'

    def action_close(self):
        self.state = 'close'

    def action_draft(self):
        self.state = 'draft'


class WorkShiftScheduleLine(models.Model):
    _name = 'hr.contract.work.schedule.line'

    work_sched_id = fields.Many2one('hr.contract.work.schedule')
    resource_calendar_id = fields.Many2one(related='work_sched_id.resource_calendar_id', model='resource.calendar', store=True, ondelete='cascade')
    date = fields.Date()
    state = fields.Selection(WORK_SCHED_STATE, default='draft')


class DayOffCalendar(models.Model):
    _name = 'hr.dayoff.calendar'
    _description = 'Calendar of Rest Days/Day-Off'
    _order = 'day_off_date desc'
    _rec_name = 'day_off_date'

    def _get_work_schedule(self, day_off_date=None):
        if not day_off_date:
            day_off_date = self.day_off_date
        if day_off_date:
            query = '''
                SELECT resource_calendar_id
                FROM hr_contract_work_schedule
                WHERE contract_id = %s
                    AND %s BETWEEN date_fr AND date_to
                    AND state = 'open'
            '''
            if self.contract_id:
                self.env.cr.execute(query, [self.contract_id.id, day_off_date])
                results = self.env.cr.dictfetchall()
            
                if len(results) == 1:
                    return results[0]['resource_calendar_id']
                elif len(results) > 1:
                    raise ValidationError(_("Found %s running work schedule for %s" % (len(results), self.employee_id.name)))
        return None

    @api.onchange('employee_id')
    def onchange_employee(self):
        obj_contract = self.env['hr.contract']
        self.contract_id = None
        if self.employee_id:
            contract_id = obj_contract.get_active_contract(self.employee_id, False)
            self.contract_id = contract_id
            self._compute_day_off()

    @api.multi
    @api.depends('day_off_date')
    def _compute_day_off(self):
        for obj in self:
            resource_calendar_id = None
            if obj.day_off_date:
                day_off = fields.Date.to_date(obj.day_off_date)
                obj.dayofweek = str(day_off.weekday())
                obj.fiscal_year = str((day_off).isocalendar()[0])
                obj.week_no = (day_off).isocalendar()[1]

                if obj.contract_id:
                    if obj.contract_id.work_shift_fix:
                        obj.resource_calendar_id = obj.contract_id.resource_calendar_id.id
                    else:
                        obj.resource_calendar_id = self._get_work_schedule(obj.day_off_date)

    @api.multi
    def name_get(self):
        res = super(DayOffCalendar, self).name_get()
        for obj in self:
            day_off = fields.Date.to_date(obj.day_off_date)
            dow = [d[1] for d in DOW if d[0] == obj.dayofweek][0]
            name = "%s - %s" % (dow, (day_off).strftime('%m/%d/%Y'))
            res.append((obj.id, name))
        return res

    employee_id = fields.Many2one('hr.employee', string='Employee')
    contract_id = fields.Many2one('hr.contract', string='Contract')
    payroll_schedule = fields.Selection(related='contract_id.payroll_schedule', store=True)
    department_id = fields.Many2one('hr.department', related='contract_id.department_id', store=True)
    resource_calendar_id = fields.Many2one('resource.calendar', string='Work Schedule')
    day_off_date = fields.Date(string='Day-Off Date', default=lambda *d: date.today())
    dayofweek = fields.Selection(DOW, compute=_compute_day_off, string='Day of Week', store=True)
    week_no = fields.Integer(compute=_compute_day_off, store=True)
    fiscal_year = fields.Char(compute=_compute_day_off, store=True)
    notes = fields.Text()


class DayOffcheduling(models.TransientModel):
    _name = 'dayoff.scheduling'

    day_off_date = fields.Date(string='Day-Off Date', required=True, default=lambda *d: date.today())
    employee_ids = fields.Many2many(comodel_name='hr.employee', required=True)

    @api.multi
    def apply_dayoff(self):
        obj_dayoff = self.env['hr.dayoff.calendar']
        for emp in self.employee_ids:
            vals = {
                'employee_id': emp.id,
                'contract_id': self.env['hr.contract'].get_active_contract(emp, False),
                'day_off_date': self.day_off_date
            }

            new_dayoff = obj_dayoff.create(vals)
            new_dayoff._compute_day_off()

        return {'type': 'ir.actions.act_window_close'}
