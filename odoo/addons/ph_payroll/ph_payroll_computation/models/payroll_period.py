from odoo import models, fields, api, tools, _
from odoo.addons.ph_payroll_contract.models.contract import EmployeeContract as contract
from odoo.exceptions import ValidationError
from datetime import date


class PayrollPeriod(models.Model):
    _name = 'hr.payroll.period'
    _description = 'Payroll Period'
    _order = 'period_fr desc'

    STATE = [
        ('draft', 'Draft'),
        ('confirm', 'Confirmed')
    ]

    PERIOD_TYPE = [
        ('1st', '1st Half'),
        ('2nd', '2nd Half')
    ]

    @api.one
    @api.depends('period_fr', 'period_to', 'period_type')
    def _get_name(self):
        fr = str(self.period_fr).split('-')
        to = str(self.period_to).split('-')
        period_fr = str(date(int(fr[0]), int(fr[1]), int(fr[2])).strftime('%m/%d/%Y'))
        period_to = str(date(int(to[0]), int(to[1]), int(to[2])).strftime('%m/%d/%Y'))
        self.name = self.period_type + ' Half (' + period_fr + ' - ' + period_to + ')'

    @api.multi
    @api.depends('period_fr')
    def _get_fiscal_year(self):
        obj_fy = self.env['account.fiscal.year']
        for obj in self:
            args = [
                ('date_from', '<=', obj.period_fr),
                ('date_to', '>=', obj.period_fr)
            ]
            fy = obj_fy.search(args, limit=1)
            obj.fiscal_year_id = fy.id or None

    name = fields.Char(compute='_get_name', store=True, string='Period')
    period_fr = fields.Date(string='From', required=True)
    period_to = fields.Date(string='To', required=True)
    period_type = fields.Selection(PERIOD_TYPE, default='1st', required=True)
    state = fields.Selection(STATE, default='draft')
    period_date_ids = fields.One2many('hr.payroll.period.date', 'payroll_period_id')
    fiscal_year_id = fields.Many2one('account.fiscal.year', compute=_get_fiscal_year, store=True)
    payroll_schedule = fields.Selection(contract.PAYROLL_SCHEDULE, default='3_sm', required=True)

    def payroll_period_name_full(self):
        sched = [v for k, v in contract.PAYROLL_SCHEDULE if k == self.payroll_schedule][0]
        name = '%s: %s' % (sched, self.name)
        return name

    def _check_overlapping(self):
        period_fr = fields.Date.to_string(self.period_fr)
        period_to = fields.Date.to_string(self.period_to)
        payroll_sched = [v for k, v in contract.PAYROLL_SCHEDULE if k == self.payroll_schedule][0]

        clause_1 = ['&', ('period_to', '<=', period_to), ('period_to', '>=', period_fr)]
        clause_2 = ['&', ('period_fr', '<=', period_to), ('period_fr', '>=', period_fr)]
        clause_3 = ['&', ('period_fr', '<=', period_fr), '|', ('period_to', '=', False), ('period_to', '>=', period_to)]
        clause_final = [('payroll_schedule', '=', self.payroll_schedule), ('state', '=', 'confirm'), '|', '|'] + clause_1 + clause_2 + clause_3
        
        pp = self.search(clause_final, limit=1)
        if pp:
            raise ValidationError(_("Payroll Period overlaps with current period '%s: %s - %s'" % (
                payroll_sched, (pp.period_fr).strftime('%m/%d/%Y'), (pp.period_to).strftime('%m/%d/%Y'))))

    def state_confirm(self):
        self._check_overlapping()
        self.period_date_ids = None
        obj_leave = self.env['hr.leave']
        fr = fields.Date.to_date(self.period_fr)
        to = fields.Date.to_date(self.period_to)
        for d in obj_leave._parse_dates(fr, to):
            vals = {
                'payroll_period_id': self.id,
                'date': d,
                'dayofweek': str(d.weekday())
            }
            self.period_date_ids = [(0, 0, vals)]

        self.state = 'confirm'

    def state_draft(self):
        self.state = 'draft'

    def _get_payroll_period(self, payroll_schedule, date):
        args = [
            ('payroll_schedule', '=', payroll_schedule),
            ('period_fr', '<=', date),
            ('period_to', '>=', date),
            ('state', '=', 'confirm')
        ]
        period = self.search(args, limit=1)
        return period

    def _get_previous_period(self, payroll_schedule, curr_pay_period):
        args = [
            ('payroll_schedule', '=', payroll_schedule),
            ('period_fr', '<', curr_pay_period.period_fr),
            ('state', '=', 'confirm')
        ]
        period = self.search(args, order='period_fr desc', limit=1)
        return period


class PayrollPeriodDate(models.Model):
    _name = 'hr.payroll.period.date'
    _order = 'date'

    DOW = [
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ]

    payroll_period_id = fields.Many2one('hr.payroll.period', string='Payroll Period', ondelete='cascade')
    date = fields.Date()
    dayofweek = fields.Selection(DOW, string='Day of Week')
    allow_late = fields.Boolean()
    allow_undertime = fields.Boolean()
    memo = fields.Text()
