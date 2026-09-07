from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil import parser as dateutil_parser
from datetime import datetime, date
from lxml import etree
import operator

import logging
_logger = logging.getLogger(__name__)


OT_TYPE = [
    ('regular_ot', 'Regular OT'),

    ('dayoff', 'Day-Off'),
    ('dayoff_ot', 'Day-Off - OT'),

    ('spc_hol', 'Special Holiday'),
    ('spc_hol_ot', 'Special Holiday - OT'),
    ('spc_hol_dayoff', 'Special Holiday - Day-Off'),
    ('spc_hol_dayoff_ot', 'Special Holiday - Day-Off OT'),

    ('leg_hol', 'Regular Holiday'),
    ('leg_hol_ot', 'Regular Holiday - OT'),
    ('leg_hol_dayoff', 'Regular Holiday Day-Off'),
    ('leg_hol_dayoff_ot', 'Regular Holiday Day-Off - OT'),

    ('double_hol', 'Double Holiday'),
    ('double_hol_ot', 'Double Holiday - OT'),
    ('double_hol_dayoff', 'Double Holiday Day-Off'),
    ('double_hol_dayoff_ot', 'Double Holiday Day-Off - OT')
]

GROUPING = [
    ('regular', 'REGULAR'),
    ('dayoff', 'DAY-OFF'),
    ('special', 'SPECIAL HOL.'),
    ('legal', 'REGULAR HOL.'),
    ('double', 'DOUBLE HOL.'),
]

STATE = [
    ('draft', 'Draft'),
    ('confirm', 'Confirmed'),
    ('pre_approve', 'Pre-approved'),
    ('approve', 'Approved')
]

class OvertimeComputation(models.Model):
    _name = 'hr.overtime.computation'
    _order = 'sequence'
    _description = 'Pay Rates Computation Table'

    TYPE = [
        ('hourly', 'Hourly Rate'),
        ('daily', 'Daily Rate')
    ]

    OPERATOR = [
        ('*', '*'),
        ('/', '/'),
        ('+', '+'),
        ('-', '-')
    ]

    # @api.multi
    # @api.depends('name', 'rate')
    # def name_get(self):
    #     res = []
    #     for r in self:
    #         name = "%s (%s)" % (r.name, '{:.2f}'.format(r.rate))
    #         res += [(r.id, name)]
    #     return res

    sequence = fields.Integer()
    name = fields.Char(required=True)
    rate_type = fields.Selection(TYPE, required=True, default='daily')
    operator = fields.Selection(OPERATOR, required=True, default='/')
    value = fields.Float(required=True, default=8.0)
    rate = fields.Float(string='Rate (%)', required=True, default=1.0, digits=(12,3))
    ga_debit_account_id = fields.Many2one('account.account', string='Debit Account')
    journal_id = fields.Many2one('account.journal', string='Journal')
    ot_type = fields.Selection(OT_TYPE, required=True, string='Type of OT')
    ot_group = fields.Selection(GROUPING, required=True, string='Grouping', default='regular')

    def compute_rate(self, computation_id, amount, wage_type='daily', holiday=False):
        def _operator(op, val1, val2):
            ops = {
                '*': operator.mul,
                '/': operator.truediv,
                '+': operator.add,
                '-': operator.sub
            }
            return ops[op](val1, val2)

        rate = 0
        ot_comp = self.browse(computation_id)
        if ot_comp:
            less_day_pay = 0
            if wage_type=='monthly' or holiday:
                less_day_pay = 1.0
            rate = _operator(ot_comp.operator, amount, ot_comp.value) * (ot_comp.rate - less_day_pay)
        return rate


class Overtime(models.Model):
    _name = 'hr.overtime'
    _order = 'ot_to desc, ot_fr desc'
    _description = 'Overtime Request'

    DOW = [
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ]

    @api.onchange('employee_id', 'ot_fr')
    def onchange_employee(self):
        self.contract_id = self.env['hr.contract'].get_active_contract(self.employee_id, False)
        pp = self.env['hr.payroll.period']._get_payroll_period(self.contract_id.payroll_schedule, self.ot_fr)
        self.payroll_period_id = pp.id if pp else None

    def _compute_ot_hrs(self, date_fr=None, date_to=None):
        obj_att = self.env['hr.attendance']
        if date_fr and date_to:
            ot_fr = obj_att._localize_dt(date_fr)
            ot_fr = fields.Datetime.to_string(ot_fr)
            new_ot_fr = dateutil_parser.parse(ot_fr)
            new_ot_fr = new_ot_fr.replace(second=0)

            ot_to = obj_att._localize_dt(date_to)
            ot_to = fields.Datetime.to_string(ot_to)
            new_ot_to = dateutil_parser.parse(ot_to)
            new_ot_to = new_ot_to.replace(second=0)

            diff_in = new_ot_to - new_ot_fr
            add_sec = 0
            if self.sched_out >= 23.9:
                add_sec = 60
            return (diff_in.total_seconds() - add_sec) / 3600.0

    # @api.multi
    @api.onchange('ot_fr', 'ot_to', 'with_break')
    def onchange_compute_ot(self):
        obj_att = self.env['hr.attendance']
        # for obj in self:
        self.ot_hours = 0
        if self.ot_fr:
            ot_date = fields.Date.to_date(obj_att._localize_dt(self.ot_fr))
            self._get_dayoff(ot_date)
            self._get_holiday(ot_date)

        if self.ot_fr and self.ot_to:
            # ot_hours = self._compute_ot_hrs(self.ot_fr, self.ot_to)
            # if ot_hours > 0:
            #     self.ot_hours = ot_hours

            y, m, d = str(fields.Date.to_string(ot_date)).split('-')
            ot_day = date(int(y), int(m), int(d))
            self.dayofweek = str(ot_day.weekday())

            self._work_sched()
            self._compute_nd()
            self._get_computation()

            total_ot = 0
            for c in self.computation_ids:
                total_ot += c.ot_hours
            self.ot_hours = total_ot

    @api.onchange('ot_fr', 'ot_to')
    def onchange_fr_to(self):
        if self.ot_hours >= 9:
            self.with_break = True
        else:
            self.with_break = False

    def _get_dayoff(self, date):
        obj_dayoff = self.env['hr.dayoff.calendar']
        dayoff = obj_dayoff.search([('employee_id', '=', self.employee_id.id), ('day_off_date', '=', date)])
        if dayoff:
            self.dayoff = True
        else:
            obj_att = self.env['hr.attendance']
            str_date = str(date) + ' 00:00:00'
            new_date = fields.Datetime.to_datetime(str_date)
            ws_obj = obj_att._get_work_schedule(contract_id=self.contract_id.id, check_in_date=new_date)['work_sched_obj']
            if ws_obj:
                self.dayoff = ws_obj.get_do_from_work_sched(date)
            else:
                self.dayoff = False

    def _get_holiday(self, date):
        self.holiday_ids = None
        obj_holiday = self.env['hr.holiday']
        holiday = obj_holiday.search([('date', '=', date)])
        self.holiday = bool(holiday)
        holiday_ids = [h.id for h in holiday]
        self.holiday_ids = [(6, 0, holiday_ids)]

    def _sched_out(self):
        obj_att = self.env['hr.attendance']
        ot_fr = obj_att._localize_dt(self.ot_fr)
        date_ot_fr = fields.Date.to_string(ot_fr)
        sched_out_combine = date_ot_fr + ' ' + obj_att._format_sched_time(self.sched_out)
        new_sched_out = dateutil_parser.parse(sched_out_combine)
        new_sched_out = new_sched_out.replace(tzinfo=None)
        return fields.Datetime.to_datetime(new_sched_out)

    def _compute_nd_hrs(self):
        obj_att = self.env['hr.attendance']
        nd_hrs = 0

        ot_fr = obj_att._localize_dt(self.ot_fr)
        check_in_hr = int(ot_fr.strftime('%H'))
        check_in_min = int(ot_fr.strftime('%M')) / 60.0
        check_in_hr_min = check_in_hr + check_in_min

        ot_to = obj_att._localize_dt(self.ot_to)
        check_out_hr = int(ot_to.strftime('%H'))
        check_out_min = int(ot_to.strftime('%M')) / 60.0
        check_out_hr_min = check_out_hr + check_out_min

        diff = (self.ot_to - self.ot_fr)
        if diff.total_seconds() > 0:
            check_date = obj_att._format_time_in_out(check_in_hr_min, check_out_hr_min)
            if check_date['time_in'] > 0 and check_date['time_out'] > 0:
                nd_hrs = (check_date['time_out'] - check_date['time_in'])
        return nd_hrs

    def _get_computation(self):
        self.computation_ids = None
        comp = None
        obj_att = self.env['hr.attendance']

        local_ot_fr = obj_att._localize_dt(self.ot_fr)
        ot_fr = local_ot_fr.replace(tzinfo=None)

        local_ot_to = obj_att._localize_dt(self.ot_to)
        ot_to = local_ot_to.replace(tzinfo=None)

        ot_hrs_list = []
        nd_hrs = self._compute_nd_hrs()

        if not self.dayoff and not self.holiday:
            if ot_fr < self._sched_out():
                overtime = self._compute_ot_hrs(ot_fr, self._sched_out())
                if self.with_break:
                    overtime -= 1
                if overtime >= 1:
                    ot_hrs_list.append([0, 0, {
                        'ot_hours': overtime,
                        'computation_id': self.env.ref('ph_payroll_overtime.ot_regular').id
                    }])
            if ot_to > self._sched_out():
                overtime = self._compute_ot_hrs(self._sched_out(), ot_to)
                if overtime >= 1:
                    ot_hrs_list.append([0, 0, {
                        'ot_hours': overtime - nd_hrs,
                        'computation_id': self.env.ref('ph_payroll_overtime.ot_regular').id
                    }])

                if nd_hrs:
                    if overtime >= 1:
                        ot_hrs_list.append([0, 0, {
                            'ot_hours': nd_hrs,
                            'computation_id': self.env.ref('ph_payroll_overtime.ot_night_diff').id
                        }])

        elif self.dayoff and not self.holiday:
            overtime = self._compute_ot_hrs(ot_fr, self._sched_out())
            if ot_fr < self._sched_out():
                if self.with_break:
                    overtime -= 1
                if overtime >= 1:
                    ot_hrs_list.append([0, 0, {
                        'ot_hours': overtime,
                        'computation_id': self.env.ref('ph_payroll_overtime.ot_day_off').id
                    }])
            if ot_to > self._sched_out():
                if overtime >= 1:
                    overtime = self._compute_ot_hrs(self._sched_out(), ot_to)
                    ot_hrs_list.append([0, 0, {
                        'ot_hours': overtime - nd_hrs,
                        'computation_id': self.env.ref('ph_payroll_overtime.ot_day_off_ot').id
                    }])

                if nd_hrs:
                    if overtime >= 1:
                        ot_hrs_list.append([0, 0, {
                            'ot_hours': nd_hrs,
                            'computation_id': self.env.ref('ph_payroll_overtime.ot_day_off_ot_nd').id
                        }])

        elif not self.dayoff and self.holiday:
            for h in self.holiday_ids:
                if not h.double_holiday:
                    if h.holiday_type == 'special':
                        if ot_fr < self._sched_out():
                            if ot_to >= self._sched_out():
                                overtime = self._compute_ot_hrs(ot_fr, self._sched_out())
                            else:
                                overtime = self._compute_ot_hrs(ot_fr, ot_to)

                            if self.with_break:
                                overtime -= 1
                            if overtime >= 1:
                                ot_hrs_list.append([0, 0, {
                                    'ot_hours': overtime,
                                    'computation_id': self.env.ref('ph_payroll_overtime.ot_spc_hol').id
                                }])
                                # raise ValidationError(_('%s' % (ot_hrs_list)))

                        if ot_to > self._sched_out():
                            overtime = self._compute_ot_hrs(self._sched_out(), ot_to)
                            if overtime >= 1:
                                ot_hrs_list.append([0, 0, {
                                    'ot_hours': overtime - nd_hrs,
                                    'computation_id': self.env.ref('ph_payroll_overtime.ot_spc_hol_ot').id
                                }])

                            if nd_hrs:
                                if overtime >= 1:
                                    ot_hrs_list.append([0, 0, {
                                        'ot_hours': nd_hrs,
                                        'computation_id': self.env.ref('ph_payroll_overtime.ot_spc_hol_ot_nd').id
                                    }])
                    else:
                        if ot_fr < self._sched_out():
                            if ot_to >= self._sched_out():
                                overtime = self._compute_ot_hrs(ot_fr, self._sched_out())
                            else:
                                overtime = self._compute_ot_hrs(ot_fr, ot_to)

                            if self.with_break:
                                overtime -= 1
                            if overtime >= 1:
                                ot_hrs_list.append([0, 0, {
                                    'ot_hours': overtime,
                                    'computation_id': self.env.ref('ph_payroll_overtime.ot_leg_hol').id
                                }])
                        if ot_to > self._sched_out():
                            overtime = self._compute_ot_hrs(self._sched_out(), ot_to)
                            if overtime >= 1:
                                ot_hrs_list.append([0, 0, {
                                    'ot_hours': overtime - nd_hrs,
                                    'computation_id': self.env.ref('ph_payroll_overtime.ot_leg_hol_ot').id
                                }])

                            if nd_hrs:
                                if overtime >= 1:
                                    ot_hrs_list.append([0, 0, {
                                        'ot_hours': nd_hrs,
                                        'computation_id': self.env.ref('ph_payroll_overtime.ot_leg_hol_ot_nd').id
                                    }])
                else:
                    if ot_fr < self._sched_out():
                        if ot_to >= self._sched_out():
                            overtime = self._compute_ot_hrs(ot_fr, self._sched_out())
                        else:
                            overtime = self._compute_ot_hrs(ot_fr, ot_to)

                        if self.with_break:
                            overtime -= 1
                        if overtime >= 1:
                            ot_hrs_list.append([0, 0, {
                                'ot_hours': overtime,
                                'computation_id': self.env.ref('ph_payroll_overtime.ot_double_hol').id
                            }])
                    if ot_to > self._sched_out():
                        overtime = self._compute_ot_hrs(self._sched_out(), ot_to)
                        if overtime >= 1:
                            ot_hrs_list.append([0, 0, {
                                'ot_hours': overtime - nd_hrs,
                                'computation_id': self.env.ref('ph_payroll_overtime.ot_double_hol_ot').id
                            }])

                        if nd_hrs:
                            if overtime >= 1:
                                ot_hrs_list.append([0, 0, {
                                    'ot_hours': nd_hrs,
                                    'computation_id': self.env.ref('ph_payroll_overtime.ot_double_hol_ot_nd').id
                                }])

        elif self.dayoff and self.holiday:
            for h in self.holiday_ids:
                if not h.double_holiday:
                    if h.holiday_type == 'special':
                        if ot_fr < self._sched_out():
                            if ot_to >= self._sched_out():
                                overtime = self._compute_ot_hrs(ot_fr, self._sched_out())
                            else:
                                overtime = self._compute_ot_hrs(ot_fr, ot_to)

                            if self.with_break:
                                overtime -= 1
                            if overtime >= 1:
                                ot_hrs_list.append([0, 0, {
                                    'ot_hours': overtime,
                                    'computation_id': self.env.ref('ph_payroll_overtime.ot_spc_hol_dayoff').id
                                }])
                        if ot_to > self._sched_out():
                            overtime = self._compute_ot_hrs(self._sched_out(), ot_to)
                            if overtime >= 1:
                                ot_hrs_list.append([0, 0, {
                                    'ot_hours': overtime - nd_hrs,
                                    'computation_id': self.env.ref('ph_payroll_overtime.ot_spc_hol_dayoff_ot').id
                                }])

                            if nd_hrs:
                                if overtime >= 1:
                                    ot_hrs_list.append([0, 0, {
                                        'ot_hours': nd_hrs,
                                        'computation_id': self.env.ref('ph_payroll_overtime.ot_spc_hol_dayoff_ot_nd').id
                                    }])
                    else:
                        if ot_fr < self._sched_out():
                            if ot_to >= self._sched_out():
                                overtime = self._compute_ot_hrs(ot_fr, self._sched_out())
                            else:
                                overtime = self._compute_ot_hrs(ot_fr, ot_to)

                            if self.with_break:
                                overtime -= 1
                            if overtime >= 1:
                                ot_hrs_list.append([0, 0, {
                                    'ot_hours': overtime,
                                    'computation_id': self.env.ref('ph_payroll_overtime.ot_leg_hol_dayoff').id
                                }])
                        if ot_to > self._sched_out():
                            overtime = self._compute_ot_hrs(self._sched_out(), ot_to)
                            if overtime >= 1:
                                ot_hrs_list.append([0, 0, {
                                    'ot_hours': overtime - nd_hrs,
                                    'computation_id': self.env.ref('ph_payroll_overtime.ot_leg_hol_dayoff_ot').id
                                }])

                            if nd_hrs:
                                if overtime >= 1:
                                    ot_hrs_list.append([0, 0, {
                                        'ot_hours': nd_hrs,
                                        'computation_id': self.env.ref('ph_payroll_overtime.ot_leg_hol_dayoff_ot_nd').id
                                    }])
                else:
                    if ot_fr < self._sched_out():
                        if ot_to >= self._sched_out():
                            overtime = self._compute_ot_hrs(ot_fr, self._sched_out())
                        else:
                            overtime = self._compute_ot_hrs(ot_fr, ot_to)
                        if self.with_break:
                            overtime -= 1
                        if overtime >= 1:
                            ot_hrs_list.append([0, 0, {
                                'ot_hours': overtime,
                                'computation_id': self.env.ref('ph_payroll_overtime.ot_double_hol_dayoff').id
                            }])
                    if ot_to > self._sched_out():
                        overtime = self._compute_ot_hrs(self._sched_out(), ot_to)
                        if overtime >= 1:
                            ot_hrs_list.append([0, 0, {
                                'ot_hours': overtime - nd_hrs,
                                'computation_id': self.env.ref('ph_payroll_overtime.ot_double_hol_dayoff_ot').id
                            }])

                        if nd_hrs:
                            if overtime >= 1:
                                ot_hrs_list.append([0, 0, {
                                    'ot_hours': nd_hrs,
                                    'computation_id': self.env.ref('ph_payroll_overtime.ot_double_hol_dayoff_ot_nd').id
                                }])

        self.computation_ids = ot_hrs_list

    def _compute_nd(self):
        self.night_diff = False
        obj_att = self.env['hr.attendance']
        ot_fr = obj_att._localize_dt(self.ot_fr)
        fr_hr = int(ot_fr.strftime('%H'))
        fr_min = int(ot_fr.strftime('%M')) / 60.0
        ot_fr_hr_min = fr_hr + fr_min

        ot_to = obj_att._localize_dt(self.ot_to)
        to_hr = int(ot_to.strftime('%H'))
        to_min = int(ot_to.strftime('%M')) / 60.0
        ot_to_hr_min = to_hr + to_min

        if ot_fr_hr_min > 22 and ot_fr_hr_min <= 24 or ot_to_hr_min > 22 and ot_to_hr_min <= 24 or \
            ot_fr_hr_min >= 0 and ot_fr_hr_min < 6 or ot_to_hr_min >= 0 and ot_to_hr_min < 6:
            self.night_diff = True

    def _work_sched(self):
        obj_att = self.env['hr.attendance']
        obj_cal = self.env['resource.calendar']
        obj_res_cal_att = self.env['resource.calendar.attendance']

        # cin = obj_att._localize_dt(self.ot_fr)
        ws = obj_att._get_work_schedule(self.contract_id.id, check_in_date=self.ot_fr)

        no_work_sched = 'No work schedule found for this date - %s' % (self.employee_id.name)

        if ws['work_sched_id']:
            self.resource_calendar_id = ws['work_sched_id']

            args = [
                ('calendar_id', '=', ws['work_sched_id']),
                ('dayofweek', '=', self.dayofweek)
            ]

            res_cal_att = obj_res_cal_att.search(args, order='dayofweek')
            if res_cal_att:
                if len(res_cal_att) == 1:
                    self.sched_in = res_cal_att[0].hour_from
                    self.sched_out = res_cal_att[0].hour_to
                else:
                    self.sched_in = res_cal_att[0].hour_from
                    self.sched_out = res_cal_att[1].hour_to
            else:
                raise ValidationError(_(no_work_sched))
        else:
            raise ValidationError(_(no_work_sched))

    @api.multi
    def name_get(self):
        obj_att = self.env['hr.attendance']
        res = super(Overtime, self).name_get()
        for obj in self:
            name = '%s [ %s ]' % (obj.employee_id.name, obj_att._format_sched_time(obj.ot_hours))
            res.append((obj.id, name))
        return res

    @api.model
    def _default_employee(self):
        if self.env.uid > 2:
            return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        else:
            return None

    # @api.onchange('with_break')
    # def onchange_with_break(self):
    #     # if not self.with_break:
    #     #     self.ot_hours = self._compute_ot_hrs(self.ot_fr, self.ot_to)
    #     # else:
    #     #     self.ot_hours = self._compute_ot_hrs(self.ot_fr, self.ot_to) - 1
    #     self._get_computation()

    @api.multi
    def copy(self):
        raise ValidationError('Duplicate action is not allowed in Overtime Requests')

    employee_id = fields.Many2one('hr.employee', string='Employee', default=_default_employee, required=True)
    user_id = fields.Many2one(related='employee_id.user_id', model='res.users', string='User', store=True)
    contract_id = fields.Many2one('hr.contract')
    wage_type = fields.Selection(related='contract_id.wage_type', store=True)
    payroll_period_id = fields.Many2one('hr.payroll.period', string='Payroll Period', required=True)
    computation_id = fields.Many2one('hr.overtime.computation', string='Computation', required=False)
    ot_fr = fields.Datetime(string='From', required=True)
    ot_to = fields.Datetime(string='To', required=True)
    # ot_hours = fields.Float(compute=_compute_ot, string='Duration (HH:MM)', store=True)
    ot_hours = fields.Float('Duration (HH:MM)')
    state = fields.Selection(STATE, default='draft')
    ot_group = fields.Selection(GROUPING, string='Grouping')
    dayoff = fields.Boolean(string='Day-Off')
    holiday = fields.Boolean(string='Is Holiday')
    holiday_ids = fields.Many2many(comodel_name='hr.holiday', string='Holidays')
    night_diff = fields.Boolean('Night Diff.')
    notes = fields.Text()
    with_break = fields.Boolean()
    resource_calendar_id = fields.Many2one('resource.calendar', 'Work Schedule')
    sched_in = fields.Float('Sched. In')
    sched_out = fields.Float('Sched. Out')
    dayofweek = fields.Selection(DOW, string='Day of Week')
    computation_ids = fields.One2many('hr.overtime.hours', 'overtime_id', string='Computations')
    advance_filing = fields.Boolean()
    advance_ot_line_id = fields.Many2one('hr.advance.overtime.line')

    def _check_night_shift(self):
        if self.night_diff:
            if not self.contract_id.has_night_diff:
                raise ValidationError(_('This employee is not allowed for Night Differential overtime. Please go to contract to change the setting'))

    def action_confirm(self):
        if self.ot_hours <= 0:
            raise ValidationError(_('Duration must be greater or equal to 1'))

        if self.contract_id.wage_type == 'daily':
            if not self.attendance_ids:
                self._get_attendance()

        self._check_night_shift()
        self.state = 'confirm'

    def action_pre_approve(self):
        self.state = 'pre_approve'

    def action_approve(self):
        if self.ot_hours <= 0:
            raise ValidationError(_('Duration must be greater or equal to 1'))

        if self.contract_id.wage_type == 'daily':
            if not self.attendance_ids:
                self._get_attendance()
                if not self.attendance_ids:
                    raise ValidationError(_('No attendance found for this overtime request\n\nEmployee: %s' % (self.employee_id.name)))

        if not self.computation_ids:
            raise ValidationError(_('No computation found for this request'))

        self._check_night_shift()
        self.state = 'approve'

    def action_draft(self):
        self.state = 'draft'

    # def _first_8hrs_ot_comp(self):
    #     comp_ids = []
    #     comp_ids.append('ph_payroll_overtime.ot_day_off').id
    #     comp_ids.append('ph_payroll_overtime.ot_spc_hol').id
    #     comp_ids.append('ph_payroll_overtime.ot_leg_hol').id
    #     comp_ids.append('ph_payroll_overtime.ot_spc_hol_dayoff').id
    #     comp_ids.append('ph_payroll_overtime.ot_leg_hol_dayoff').id
    #     comp_ids.append('ph_payroll_overtime.ot_double_hol').id
    #     comp_ids.append('ph_payroll_overtime.ot_double_hol_dayoff').id
    #     return comp_ids


class OvertimeSummary(models.Model):
    _inherit = 'hr.overtime.summary'

    computation_id = fields.Many2one('hr.overtime.computation', string='Computation')
    ot_type = fields.Selection(related='computation_id.ot_type', string='Type of OT')
    rate = fields.Float(related='computation_id.rate')


class OvertimeHours(models.Model):
    _name = 'hr.overtime.hours'
    _rec_name = 'computation_id'

    overtime_id = fields.Many2one('hr.overtime', ondelete='cascade')
    ot_hours = fields.Float('OT Hours')
    computation_id = fields.Many2one('hr.overtime.computation', string='Computation', required=True)
    rate = fields.Float(related='computation_id.rate', store=True)


# class OTRequestMulti(models.TransientModel):
#     _name = 'ot.request.multi'

#     payroll_period_id = fields.Many2one('hr.payroll.period', required=True)
#     # attendance_ids = fields.Many2many('')
#     line_ids = fields.One2many('ot.request.multi.line', 'request_id')

#     def open_attendance_with_ot(self):
#         view_id = self.env.ref('ph_payroll_attendance.new_attendance_tree').id
#         domain = [
#             ('payroll_period_id', '=', self.payroll_period_id.id),
#             ('overtime', '>', 0),
#             ('state', '=', 'validate')
#         ]
#         vals = {
#             'type': 'ir.actions.act_window',
#             'view_type': 'tree',
#             'view_mode': 'tree',
#             'res_model': 'hr.attendance',
#             'view_id': view_id,
#             'target': 'new',
#             'domain': domain
#         }
#         return vals


# class OTRequestMultiLine(models.TransientModel):
#     _name = 'ot.request.multi.line'
#     _inherit = 'hr.overtime'

#     request_id = fields.Many2one('ot.request.multi')


class MultiAdvanceOvertime(models.Model):
    _name = 'hr.advance.overtime'

    STATE = [
        ('draft', 'Draft'),
        ('pre_approve', 'Pre-approved'),
        ('cancel', 'Cancelled')
    ]

    @api.multi
    def unlink(self):
        for obj in self:
            if obj.state != 'draft':
                raise ValidationError(_('You cannot delete overtime request which is not in draft state'))
        return super(MultiAdvanceOvertime, self).unlink()

    @api.multi
    @api.depends('ot_fr', 'ot_to')
    def _compute_ot(self):
        obj_ot = self.env['hr.overtime']
        for obj in self:
            obj.ot_hours = 0
            if obj.ot_fr and obj.ot_to:
                ot_hours = obj_ot._compute_ot_hrs(obj.ot_fr, obj.ot_to)
                if ot_hours > 0:
                    obj.ot_hours = ot_hours

    def _ot_from(self):
        return (datetime.utcnow()).strftime('%Y-%m-%d 9:00:00')

    def _ot_to(self):
        return (datetime.utcnow()).strftime('%Y-%m-%d 11:00:00')

    @api.multi
    def name_get(self):
        obj_att = self.env['hr.attendance']
        res = []
        for obj in self:
            fr = obj_att._localize_dt(obj.ot_fr).strftime('%m/%d/%Y %I:%M %p') if obj.ot_fr else '-'
            to = obj_att._localize_dt(obj.ot_to).strftime('%m/%d/%Y %I:%M %p') if obj.ot_to else '-'
            name = '%s to %s' % (fr, to)
            res += [(obj.id, name)]
        return res

    ot_fr = fields.Datetime('From', required=True, default=_ot_from)
    ot_to = fields.Datetime('To', required=True, default=_ot_to)
    ot_hours = fields.Float(compute=_compute_ot, string='Duration (HH:MM)', store=True)
    line_ids = fields.One2many('hr.advance.overtime.line', 'overtime_id')
    notes = fields.Text()
    state = fields.Selection(STATE, default='draft')

    def select_employees(self):
        self.line_ids = None
        return {
            'name': 'Employee Contracts',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ot.hr.employee.contract',
            'target': 'new'
        }

    def update_hours(self):
        if not self.line_ids:
            raise ValidationError(_('Overtime requests must not be empty'))

        ctx = dict(self._context)
        for l in self.line_ids:
            l.ot_fr = self.ot_fr
            l.ot_to = self.ot_to
            l.onchange_employee()

    def create_advance_ot(self):
        obj_ot = self.env['hr.overtime']
        if not self.line_ids:
            raise ValidationError(_('Overtime requests must not be empty'))

        for l in self.line_ids:
            vals = {
                'advance_filing': True,
                'employee_id': l.employee_id.id,
                'contract_id': l.contract_id.id,
                'ot_fr': l.ot_fr,
                'ot_to': l.ot_to,
                'payroll_period_id': l.payroll_period_id.id,
                'state': 'pre_approve',
                'advance_ot_line_id': l.id
            }
            new_ot = obj_ot.create(vals)
            new_ot.onchange_compute_ot()
            l.reference_ot_id = new_ot.id

        self.state = 'pre_approve'

    def state_draft(self):
        self._remove_ref_ot()
        self.state = 'draft'

    def state_cancel(self):
        self._remove_ref_ot()
        self.state = 'cancel'

    def _remove_ref_ot(self):
        for l in self.line_ids:
            if l.reference_ot_id.state in ('draft', 'confirm', 'pre_approve'):
                l.reference_ot_id.unlink()


class MultiAdvanceOvertimeLine(models.Model):
    _name = 'hr.advance.overtime.line'

    @api.multi
    @api.depends('ot_fr', 'ot_to')
    def _compute_ot(self):
        obj_ot = self.env['hr.overtime']
        for obj in self:
            obj.ot_hours = 0
            if obj.ot_fr and obj.ot_to:
                ot_hours = obj_ot._compute_ot_hrs(obj.ot_fr, obj.ot_to)
                if ot_hours > 0:
                    obj.ot_hours = ot_hours

    overtime_id = fields.Many2one('hr.advance.overtime', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', required=True)
    contract_id = fields.Many2one('hr.contract', required=True)
    ot_fr = fields.Datetime('From')
    ot_to = fields.Datetime('To')
    ot_hours = fields.Float(compute=_compute_ot, string='Duration (HH:MM)', store=True)
    payroll_period_id = fields.Many2one('hr.payroll.period')
    reference_ot_id = fields.Many2one('hr.overtime', 'Reference OT')

    @api.onchange('employee_id', 'ot_fr')
    def onchange_employee(self):
        self.contract_id = self.env['hr.contract'].get_active_contract(self.employee_id, False)
        pp = self.env['hr.payroll.period']._get_payroll_period(self.contract_id.payroll_schedule, self.ot_fr)
        self.payroll_period_id = pp.id if pp else None


class OTMultiEmployeeContract(models.TransientModel):
    _name = 'ot.hr.employee.contract'

    overtime_id = fields.Many2one('hr.advance.overtime')
    contract_ids = fields.Many2many(comodel_name='hr.contract')

    def load_contracts(self):
        ctx = dict(self._context)
        obj_ot_line = self.env['hr.advance.overtime.line']
        if not self.contract_ids:
            raise ValidationError(_('Contracts should not be empty'))

        adv_ot = None
        if 'default_overtime_id' in ctx:
            obj_adv_ot = self.env['hr.advance.overtime']
            adv_ot = obj_adv_ot.browse(ctx['default_overtime_id'])

        pp = None
        if adv_ot: adv_ot.line_ids = None

        for c in self.contract_ids:
            if adv_ot:
                pp = self.env['hr.payroll.period']._get_payroll_period(c.payroll_schedule, adv_ot.ot_fr)
            vals = {
                'employee_id': c.employee_id.id,
                'contract_id': c.id,
                'overtime_id': ctx['default_overtime_id'],
                'ot_fr': adv_ot.ot_fr if adv_ot else None,
                'ot_to': adv_ot.ot_to if adv_ot else None,
                'payroll_period_id': pp.id if pp else None
            }
            obj_ot_line.create(vals)


class OvertimeState(models.TransientModel):
    _name = 'overtime.state'

    @api.multi
    def _get_overtime(self):
        active_ids = self._context.get('active_ids')
        return [(6, 0, active_ids)]
    
    overtime_ids = fields.Many2many(comodel_name='hr.overtime', string='Overtime Requests', default=_get_overtime)
    state = fields.Selection(STATE, default='draft')

    def change_state(self):
        obj_ot = self.env['hr.overtime']
        if self.overtime_ids:
            for ot in self.overtime_ids:
                if self.state == 'draft':
                    ot.state = 'draft'
                elif self.state == 'confirm':
                    ot.action_confirm()
                elif self.state == 'pre_approve':
                    ot.state = 'pre_approve'
                else:
                    ot.action_approve()                
        else:
            raise ValidationError(_('Overtime request must not be empty'))
