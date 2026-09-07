from odoo import models, fields, api, tools, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError, UserError
from pytz import timezone
from datetime import date
from dateutil import parser as dateutil_parser
from dateutil.relativedelta import relativedelta
import datetime

import logging
_logger = logging.getLogger(__name__)


DAY_PERIOD = [
    ('morning', 'Morning'),
    ('afternoon', 'Afternoon')
]

STATE = [
    ('draft', 'Draft'),
    ('validate', 'Validated')
]

class Attendance(models.Model):
    _inherit = 'hr.attendance'
    _order = 'check_in desc, employee_id'

    DOW = [
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ]

    HOL_TYPE = [
        ('regular', 'Regular Holiday'),
        ('special', 'Special Holiday')
    ]

    @api.multi
    def name_get(self):
        res = []
        for obj in self:
            cin = self._localize_dt(obj.check_in).strftime('%m/%d/%Y %I:%M %p') if obj.check_in else '-'
            cout = self._localize_dt(obj.check_out).strftime('%m/%d/%Y %I:%M %p') if obj.check_out else '-'
            name = '%s to %s' % (cin, cout)
            res += [(obj.id, name)]
        return res

    def _localize_dt(self, dt):
        if dt:
            return timezone('UTC').localize(dt).astimezone(timezone('Asia/Manila'))
        else:
            return None

    def _get_work_schedule(self, contract_id=None, check_in_date=None):
        data = {
            'work_sched_obj': None,
            'work_sched_id': None,
            'work_sched_ids': []
        }

        if not self.contract_id:
            if not contract_id:
                raise ValidationError(_('No active contract found'))

        if contract_id:
            contract = self.env['hr.contract'].browse(contract_id)
        else:
            contract = self.contract_id

        if contract.work_shift_fix:
            data['work_sched_obj'] = contract.resource_calendar_id
            data['work_sched_id'] = contract.resource_calendar_id.id
            data['work_sched_ids'].append(contract.resource_calendar_id.id)
        else:
            if not check_in_date:
                cin_date = datetime.datetime.now()
            else:
                cin_date = check_in_date
            check_in = fields.Date.to_string(self._localize_dt(cin_date))

            query = '''
                SELECT resource_calendar_id
                FROM hr_contract_work_schedule
                WHERE contract_id = %s
                    AND %s BETWEEN date_fr AND date_to
                    AND state = 'open'
            '''

            self.env.cr.execute(query, [contract.id, check_in])
            results = self.env.cr.dictfetchall()

            obj_res_cal = self.env['resource.calendar']
            
            if len(results) == 1:
                data['work_sched_obj'] = obj_res_cal.browse(results[0]['resource_calendar_id'])
                data['work_sched_id'] = results[0]['resource_calendar_id']
                data['work_sched_ids'].append(results[0]['resource_calendar_id'])
            else:
                for res in results:
                    data['work_sched_ids'].append(res['resource_calendar_id'])
                data['work_sched_obj'] = obj_res_cal.browse(data['work_sched_ids'])
        return data

    def _get_employee(self, barcode='', employee_id=None):
        obj_emp = self.env['hr.employee']
        if not employee_id and barcode:
            args = [('barcode', '=', barcode)]
            emp = obj_emp.search(args)
            if not emp:
                raise ValidationError(_('No employee found with this Badge ID: %s' % (barcode)))
            return emp.id
        else:
            return obj_emp.browse(employee_id).barcode

    @api.onchange('barcode')
    def onchange_barcode(self):
        if self.barcode:
            emp_id = self._get_employee(self.barcode)
            if emp_id:
                self.employee_id = emp_id
            else:
                self.employee_id = None
                self.contract_id = None
                self.resource_calendar_id = None

    @api.onchange('employee_id', 'contract_id', 'check_in')
    def onchange_employee(self):
        self.resource_calendar_id = None
        if self.employee_id:
            if self.barcode != self.employee_id.barcode:
                self.barcode = self.employee_id.barcode

            self.contract_id = self.env['hr.contract'].get_active_contract(self.employee_id, False)

            if self.contract_id:
                if not self.check_in:
                    ws = self._get_work_schedule()
                else:
                    ws = self._get_work_schedule(check_in_date=self.check_in)
                work_sched_id = ws['work_sched_id']
                work_sched_ids = ws['work_sched_ids']

                domain = [('id', 'in', work_sched_ids)]
                return {
                        'domain': {'resource_calendar_id': domain},
                        'value': {'resource_calendar_id': work_sched_id}
                    }

    def _is_dayoff(self, employee_id, date):
        obj_dayoff = self.env['hr.dayoff.calendar']
        args = [('employee_id', '=', employee_id), ('day_off_date', '=', date)]
        do_cal = obj_dayoff.search(args)
        if do_cal:
            return True
        else:
            if self.resource_calendar_id:
                return self.resource_calendar_id.get_do_from_work_sched(date)
            else:
                return False    

    @api.multi
    @api.depends('check_in', 'check_out', 'resource_calendar_id', 'day_period', 'allow_late', 'allow_undertime')
    def _compute_worked_hours(self):
        for obj in self:
            # Pre-load active contract
            obj.contract_id = self.env['hr.contract'].get_active_contract(obj.employee_id)

            if obj.contract_id and obj.contract_id.state != 'open':
                raise ValidationError(_('Employee contract must be active or running to continue'))

            ci = co = None
            if obj.check_in:
                ci = obj._localize_dt(obj.check_in)
                obj.localize_date = fields.Date.to_date(ci)
            else:
                if obj.check_out:
                    co = obj._localize_dt(obj.check_out)
                    obj.localize_date = fields.Date.to_date(co)

            if obj.check_out:
                co = obj._localize_dt(obj.check_out)

            if ci and co:
                actual_check_in = dateutil_parser.parse(fields.Datetime.to_string(ci)).replace(tzinfo=None, second=0)
                actual_check_out = dateutil_parser.parse(fields.Datetime.to_string(co)).replace(tzinfo=None, second=0)
                delta = actual_check_out - actual_check_in
                obj.total_worked_hours = (delta.total_seconds() / 3600.0)

            cd = None
            if ci:
                cd = ci
            else:
                cd = co

            if cd:
                pp = self.env['hr.payroll.period']._get_payroll_period(obj.contract_id.payroll_schedule, cd)
                if pp:
                    obj.payroll_period_id = pp.id

            if ci:
                y, m, d = str(fields.Date.to_string(ci)).split('-')
                ci_date = date(int(y), int(m), int(d))
                obj.dayofweek = str(ci_date.weekday())
                obj._get_work_hours()

                # Compute late, udertime, overtime
                self._compute_time(
                        fields.Datetime.to_string(ci),
                        fields.Datetime.to_string(co),
                        fields.Date.to_string(ci),
                        fields.Date.to_string(co)
                    )
            else:
                if co:
                    y, m, d = str(fields.Date.to_string(co)).split('-')
                    co_date = date(int(y), int(m), int(d))
                    obj.dayofweek = str(co_date.weekday())

            obj.onchange_check_in_out_holiday()

            # Compute night differential
            if ci and co:
                if obj.contract_id.has_night_diff:
                    self._compute_night_diff(ci, co)

    @api.multi
    @api.depends('check_in')
    def _compute_late_undertime(self):
        for obj in self:
            if obj.check_in:
                if obj.payroll_period_id:
                    for pd in obj.payroll_period_id.period_date_ids:
                        check_in = fields.Date.to_date(obj._localize_dt(obj.check_in))
                        if pd.date == check_in:
                            obj.allow_late = pd.allow_late
                            obj.allow_undertime = pd.allow_undertime
                            obj.memo = pd.memo

    def _format_sched_time(self, hours):
        return (str(datetime.timedelta(hours=hours))[:-3]).zfill(5)

    @api.multi
    def _compute_time(self, check_in, check_out, date_in, date_out):
        for obj in self:
            obj.late = obj.undertime = obj.overtime = 0
            if check_in and obj.resource_calendar_id:
                sched_time_in = obj.hour_from + obj.grace_period
                if sched_time_in >= 24.0:
                    raise UserError(_('Scheduled Time IN or Grace Period is not correctly set'))

                # LATE
                sched_in_combine = date_in + ' ' + obj._format_sched_time(sched_time_in)
                new_sched_in = dateutil_parser.parse(sched_in_combine)
                new_sched_in = new_sched_in.replace(tzinfo=None)
                sched_in = fields.Datetime.to_datetime(new_sched_in)
                actual_check_in = dateutil_parser.parse(check_in)
                actual_check_in = actual_check_in.replace(tzinfo=None, second=0)
                diff_in = (actual_check_in - sched_in)
                late = diff_in.total_seconds() / 3600.0

                if late < 0 and abs(late) >= 8:
                    sched_in = sched_in - relativedelta(days=1)
                    diff_in = (actual_check_in - sched_in)
                    late = diff_in.total_seconds() / 3600.0                    

                if not obj.allow_late and late > 0:
                    obj.late = late

            if check_out and obj.resource_calendar_id:
                sched_time_out = obj.hour_to
                if sched_time_out >= 24.0:
                    raise UserError(_('Scheduled Time OUT is not correctly set'))

                # UNDERTIME
                sched_out_combine = date_out + ' ' + obj._format_sched_time(sched_time_out)
                new_sched_out = dateutil_parser.parse(sched_out_combine)
                new_sched_out = new_sched_out.replace(tzinfo=None)
                sched_out = fields.Datetime.to_datetime(new_sched_out)
                actual_check_out = dateutil_parser.parse(check_out)
                actual_check_out = actual_check_out.replace(tzinfo=None, second=0)
                diff_out = (sched_out - actual_check_out)

                add_sec = 0
                if sched_time_out >= 23.9:
                    add_sec = 60
                
                undertime = (diff_out.total_seconds() + add_sec) / 3600.0
                if not obj.allow_undertime and undertime > 0:
                    if undertime <= 8:
                        obj.undertime = undertime

                # OVERTIME
                sched_out_combine = date_in + ' ' + obj._format_sched_time(sched_time_out)
                new_sched_out = dateutil_parser.parse(sched_out_combine)
                new_sched_out = new_sched_out.replace(tzinfo=None)
                sched_out = fields.Datetime.to_datetime(new_sched_out)
                diff_out = (actual_check_out - sched_out)

                overtime = (diff_out.total_seconds() - add_sec) / 3600.0
                if overtime > 0:
                    if overtime >= 1 and overtime <= 8:
                        obj.overtime = overtime
                    else:
                        if overtime >= 24:
                            obj.overtime = (overtime - 24)

            if check_in and check_out:
                obj.dayoff = self._is_dayoff(obj.employee_id.id, obj.localize_date)
                if obj.dayoff and obj.total_worked_hours > 0:
                    obj.overtime = obj.total_worked_hours

    @api.multi
    def _compute_night_diff(self, check_in, check_out):
        for obj in self:
            obj.night_diff = 0

            check_in_hr = int(check_in.strftime('%H'))
            check_in_min = int(check_in.strftime('%M')) / 60.0
            check_in_hr_min = check_in_hr + check_in_min

            check_out_hr = int(check_out.strftime('%H'))
            check_out_min = int(check_out.strftime('%M')) / 60.0
            check_out_hr_min = check_out_hr + check_out_min

            diff = (check_out - check_in)
            if diff.total_seconds() > 0:
                check_date = self._format_time_in_out(check_in_hr_min, check_out_hr_min)
                if check_date['time_in'] > 0 and check_date['time_out'] > 0:
                    obj.night_diff = (check_date['time_out'] - check_date['time_in'])

                    if obj.night_diff <= 0:
                        obj.night_diff = 0
                    else:
                        if obj.has_nd:
                            if not obj.dayoff and not obj.is_holiday:
                                obj.night_diff_rate_id = self.env.ref("ph_payroll_attendance.nd_pay_rate_reg").id
                            elif obj.dayoff and not obj.is_holiday:
                                obj.night_diff_rate_id = self.env.ref("ph_payroll_attendance.nd_pay_rate_dayoff").id
                            elif not obj.dayoff and obj.is_holiday:
                                if obj.holiday_type == 'special':
                                    obj.night_diff_rate_id = self.env.ref("ph_payroll_attendance.nd_pay_rate_spec_hol").id
                                elif obj.holiday_type == 'regular':
                                    obj.night_diff_rate_id = self.env.ref("ph_payroll_attendance.nd_pay_rate_reg_hol").id
                                if obj.double_holiday:
                                    obj.night_diff_rate_id = self.env.ref("ph_payroll_attendance.nd_pay_rate_double_hol").id
                            elif obj.dayoff and obj.is_holiday:
                                if obj.holiday_type == 'special':
                                    obj.night_diff_rate_id = self.env.ref("ph_payroll_attendance.nd_pay_rate_spec_hol_dayoff").id
                                elif obj.holiday_type == 'regular':
                                    obj.night_diff_rate_id = self.env.ref("ph_payroll_attendance.nd_pay_rate_reg_hol_dayoff").id
                                if obj.double_holiday:
                                    obj.night_diff_rate_id = self.env.ref("ph_payroll_attendance.nd_pay_rate_double_hol_dayoff").id


    @api.multi
    def _format_time_in_out(self, time_in, time_out):
        data = {
            'time_in': 0,
            'time_out': 0
        }

        if time_in >= 22 and time_in <= 24 and time_out >= 0 and time_out <= 6:
            data['time_in'] = time_in
            data['time_out'] = time_out + 24

        elif time_in >= 0 and time_in <= 6 and time_out >= 0 and time_out <= 6:
            data['time_in'] = time_in + 24
            data['time_out'] = time_out + 24

        elif time_in >= 0 and time_in <= 6 and time_out > 6:
            data['time_in'] = time_in + 24
            data['time_out'] = 30

        elif time_in >= 22 and time_in <= 24 and time_out > 6 and time_out > time_out:
            data['time_in'] = time_in
            data['time_out'] = 30

        elif time_in < 22 and time_out >= 0 and time_out <= 6:
            data['time_in'] = 22
            data['time_out'] = time_out + 24

        elif time_in < 22 and time_out >= 22 and time_out <= 24:
            data['time_in'] = 22
            data['time_out'] = time_out

        elif time_in < 22 and time_out < 22 and time_out >= 0 and time_out <= 6:
            data['time_in'] = data['time_out'] = 0

        elif time_in < 22 and time_out > 6 and time_out >= 0 and time_out <= 6:
            data['time_in'] = 22
            data['time_out'] = 30

        elif time_in < 22 and time_out > 6 and time_in > time_out:
            data['time_in'] = 22
            data['time_out'] = 30

        elif time_in >= 22 and time_out <= 24:
            data['time_in'] = time_in
            data['time_out'] = time_out

            if data['time_in'] > data['time_out'] and data['time_out'] > 6:
                data['time_out'] = 30
        return data

    def _get_work_hours(self):
        obj_res_cal_att = self.env['resource.calendar.attendance']
        args = [
            ('calendar_id', '=', self.resource_calendar_id.id),
            ('dayofweek', '=', self.dayofweek)
        ]
        if self.resource_calendar_id.regular_schedule:
            args.extend([('day_period', '=', self.day_period or 'morning')])

        res_cal_att = obj_res_cal_att.search(args, limit=1)
        if res_cal_att:
            self.hour_from = res_cal_att[0].hour_from
            self.hour_to = res_cal_att[0].hour_to
            self.has_nd = res_cal_att[0].has_nd

    @api.model
    def create(self, vals):
        ctx = dict(self._context)
        res = super(Attendance, self).create(vals)
        for r in res:
            if 'employee_id' not in vals:
                r.employee_id = self._get_employee(vals['barcode'])

            if 'barcode' not in vals:
                r.barcode = self._get_employee(employee_id=r.employee_id.id)

            if not r.contract_id or 'contract_id' not in vals:
                r.contract_id = self.env['hr.contract'].get_active_contract(r.employee_id)

            if 'payroll_period_id' not in vals:
                check_date = None
                if r.check_in:
                    check_date = self._localize_dt(r.check_in)
                else:
                    if r.check_out:
                        check_date = self._localize_dt(r.check_out)

                if check_date:
                    pp = self.env['hr.payroll.period']._get_payroll_period(r.contract_id.payroll_schedule, check_date)
                    if pp:
                        r.payroll_period_id = pp.id
                    else:
                        raise ValidationError(_("No payroll period found for the date - '%s'" % (check_date.strftime('%m/%d/%Y'))))
                else:
                    raise ValidationError(_("Check IN/OUT must be present to continue"))

            if 'localize_date' not in vals:
                r._compute_worked_hours()

            if 'kiosk' in ctx or 'multi_att' in ctx:
                ci = self._localize_dt(r.check_in)
                check_in_hr = int(ci.strftime('%H'))
                check_in_min = int(ci.strftime('%M')) / 60.0
                check_in_hr_min = check_in_hr + check_in_min
                if check_in_hr_min >= 12.25:
                    r.day_period = 'afternoon'

            if 'resource_calendar_id' not in vals:
                ws = self._get_work_schedule(contract_id=r.contract_id.id, check_in_date=r.check_in)
                work_sched_ids = ws['work_sched_ids']
                if len(work_sched_ids) > 1:
                    raise ValidationError(_('Found %s work schedule for employee - %s' % (len(work_sched_ids), r.employee_id.name)))
                elif len(work_sched_ids) == 1:
                    r.resource_calendar_id = work_sched_ids[0]
                    r.regular_schedule = r.resource_calendar_id.regular_schedule
                else:
                    raise ValidationError(_('No work schedule found'))

        return res

    @api.multi
    def unlink(self):
        for obj in self:
            if obj.state != 'draft':
                raise ValidationError(_('You cannot delete attendance which is not in draft state'))
        return super(Attendance, self).unlink()

    @api.onchange('resource_calendar_id')
    def onchange_work_schedule(self):
        self.regular_schedule = False
        if self.resource_calendar_id:
            self.regular_schedule = self.resource_calendar_id.regular_schedule

    @api.multi
    def _check_holiday(self):
        for obj in self:
            ci = obj._localize_dt(obj.check_in)
            check_in = fields.Date.to_date(ci)
            co = obj._localize_dt(obj.check_out)
            check_out = fields.Date.to_date(co)

            obj_holiday = self.env['hr.holiday']
            args = ['|', ('date', '=', check_in), ('date', '=', check_out)]
            return obj_holiday.search(args, order='date')

    @api.multi
    def onchange_check_in_out_holiday(self):
        for obj in self:
            obj.holiday_ids = None
            obj.is_holiday = False
            obj.holiday_type = None
            if obj.check_in and obj.check_out:
                holidays = obj._check_holiday()
                if holidays:
                    if obj.contract_id.has_holiday:
                        obj.is_holiday = True
                        obj.holiday_type = holidays[0].holiday_type
                        obj.double_holiday = holidays[0].double_holiday
                        for hol in holidays:
                            vals = {
                                'holiday_id': hol.id,
                                # 'holiday_rate': hol.holiday_rate,
                                # 'holiday_hours': obj.total_worked_hours - obj.night_diff,
                                # 'holiday_nd_rate': hol.holiday_nd_rate,
                                # 'holiday_nd_hours': obj.night_diff
                            }
                            obj.holiday_ids = [(0, 0, vals)]
                    else:
                        raise ValidationError(_('This employee is not allowed to work on holiday'))

    @api.model
    def _default_employee(self):
        emp = None
        if self.env.uid > 2:
            emp = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return emp

    employee_id = fields.Many2one('hr.employee', string='Employee', ondelete='cascade', default=_default_employee, index=True, required=False)
    barcode = fields.Char(string='Badge ID')
    late = fields.Float(compute=_compute_worked_hours, store=True)
    undertime = fields.Float(compute=_compute_worked_hours, store=True)
    overtime = fields.Float(compute=_compute_worked_hours, store=True)
    night_diff = fields.Float(compute=_compute_worked_hours, store=True, string='ND Hours')
    night_diff_rate_id = fields.Many2one('hr.nd.pay.rate', 'ND Pay Rate', compute=_compute_worked_hours, store=True)
    payroll_period_id = fields.Many2one('hr.payroll.period', compute=_compute_worked_hours, string='Payroll Period', store=True, required=False)
    contract_id = fields.Many2one('hr.contract', string='Contract', required=False)
    resource_calendar_id = fields.Many2one('resource.calendar', 'Schedule', required=False)
    grace_period = fields.Float(related='resource_calendar_id.grace_period', string='Grace Period', store=True)
    dayofweek = fields.Selection(DOW, compute=_compute_worked_hours, string='Day of Week', store=True)
    day_period = fields.Selection(DAY_PERIOD, required=False, default='morning')
    hour_from = fields.Float(compute=_compute_worked_hours,string='Work From', store=True)
    hour_to = fields.Float(compute=_compute_worked_hours, string='Work To', store=True)
    has_nd = fields.Boolean(compute=_compute_worked_hours, string='Has ND', store=True)
    allow_late = fields.Boolean(compute=_compute_late_undertime, store=True)
    allow_undertime = fields.Boolean(compute=_compute_late_undertime, store=True)
    memo = fields.Text(compute=_compute_late_undertime, store=True)
    regular_schedule = fields.Boolean()
    localize_date = fields.Date(compute=_compute_worked_hours, store=True, string='Attendance Date')
    total_worked_hours = fields.Float(string='Total Worked Hours', compute=_compute_worked_hours, store=True)
    # worked_hours = fields.Float(string='Actual Worked Hours', compute=_compute_worked_hours, store=True)
    holiday_ids = fields.One2many('hr.attendance.holiday', 'attendance_id', compute=_compute_worked_hours, store=True)
    is_holiday = fields.Boolean(compute=_compute_worked_hours, store=True)
    holiday_type = fields.Selection(HOL_TYPE)
    double_holiday = fields.Boolean()
    state = fields.Selection(STATE, default='draft')
    dayoff = fields.Boolean('Day-Off')

    @api.multi
    def state_validate(self):
        self.state = 'validate'

    @api.multi
    def state_draft(self):
        self.state = 'draft'


class AttendanceHoliday(models.Model):
    _name = 'hr.attendance.holiday'
    _order = 'date desc'
    _rec_name = 'holiday_id'

    attendance_id = fields.Many2one('hr.attendance', ondelete='cascade')
    payroll_period_id = fields.Many2one(related='attendance_id.payroll_period_id', model='hr.payroll.period')
    employee_id = fields.Many2one(related='attendance_id.employee_id', model='hr.employee')
    resource_calendar_id = fields.Many2one(related='attendance_id.resource_calendar_id', model='resource.calendar')
    check_in = fields.Datetime(related='attendance_id.check_in')
    check_out = fields.Datetime(related='attendance_id.check_out')
    holiday_id = fields.Many2one('hr.holiday', string='Name')
    date = fields.Date(related='holiday_id.date')
    holiday_type = fields.Selection(related='holiday_id.holiday_type', string='Holiday Type')
    
    holiday_rate = fields.Float(string='Holiday Rate', digits=(12,4))
    holiday_hours = fields.Float(string='Holiday Hours')
    holiday_nd_rate = fields.Float(string='Holiday ND Rate', digits=(12,4))
    holiday_nd_hours = fields.Float(string='Holiday ND Hours')


class Holiday(models.Model):
    _inherit = 'hr.holiday'

    attendance_ids = fields.One2many('hr.attendance.holiday', 'holiday_id')


class DailyTimeRecord(models.Model):
    _name = 'hr.employee.dtr'
    _rec_name = 'payroll_period_id'

    employee_id = fields.Many2one('hr.employee', required=True)
    barcode = fields.Char(related='employee_id.barcode', string='Badge ID', store=True)
    department_id = fields.Many2one(related='employee_id.department_id', model='hr.department', string='Department', store=True)
    payroll_period_id = fields.Many2one('hr.payroll.period', string='Payroll Period', required=True)
    dtr_line_ids = fields.One2many('hr.employee.dtr.line', 'dtr_id')
    dtr_ot_ids = fields.One2many('hr.employee.dtr.ot', 'dtr_id')

    @api.multi
    def get_dtr(self):
        self.dtr_line_ids = None
        obj_att = self.env['hr.attendance']
        args = [
            ('payroll_period_id', '=', self.payroll_period_id.id),
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'validate')
        ]
        attendance = obj_att.search(args)
        if attendance:
            contract = self.env['hr.contract'].get_active_contract(self.employee_id, False, True)
            if not contract:
                raise ValidationError(_('No active contract found'))
            if not contract.work_shift_fix:
                for pd in self.payroll_period_id.period_date_ids:
                    self.dtr_line_ids = [(0, 0, {'date': pd.date})]

                if self.dtr_line_ids:
                    for dtr in self.dtr_line_ids:
                        for att in attendance:
                            if dtr.date == att.localize_date:
                                dtr.sched_in = att.hour_from
                                dtr.time_in = att.check_in
                                dtr.sched_out = att.hour_to
                                dtr.time_out = att.check_out
                                dtr.late = att.late
                                dtr.undertime = att.undertime
                                dtr.nd = att.night_diff
                            
                            dtr.dayoff = self._get_dayoff(contract.id, dtr.date)
                            dtr.half_day = self._get_leave(dtr.date)['half_day']
                            dtr.absent = self._get_leave(dtr.date)['absent']
                            dtr.sl = self._get_leave(dtr.date)['sl']
                            dtr.vl = self._get_leave(dtr.date)['vl']
            else:
                for pd in self.payroll_period_id.period_date_ids:
                    self.dtr_line_ids = [(0, 0, {'date': pd.date, 'day_period': 'morning'})]
                    self.dtr_line_ids = [(0, 0, {'date': pd.date, 'day_period': 'afternoon'})]

                if self.dtr_line_ids:
                    for dtr in self.dtr_line_ids:
                        for att in attendance:
                            if dtr.date == att.localize_date and dtr.day_period == att.day_period:
                                dtr.sched_in = att.hour_from
                                dtr.time_in = att.check_in
                                dtr.sched_out = att.hour_to
                                dtr.time_out = att.check_out
                                dtr.late = att.late
                                dtr.undertime = att.undertime
                                dtr.nd = att.night_diff
                            
                            dtr.dayoff = self._get_dayoff(contract.id, dtr.date)
                            dtr.half_day = self._get_leave(dtr.date)['half_day']
                            dtr.absent = self._get_leave(dtr.date)['absent']
                            dtr.sl = self._get_leave(dtr.date)['sl']
                            dtr.vl = self._get_leave(dtr.date)['vl']

            self._get_ot()
        else:
            raise ValidationError(_("No valid daily time record found for employee '%s'" % (self.employee_id.name)))

    def _get_dayoff(self, contract_id, date):
        obj_dayoff = self.env['hr.dayoff.calendar']
        dayoff = obj_dayoff.search([('employee_id', '=', self.employee_id.id), ('day_off_date', '=', date)])
        if dayoff:
            return True
        else:
            obj_att = self.env['hr.attendance']
            str_date = str(date) + ' 00:00:00'
            new_date = fields.Datetime.to_datetime(str_date)
            ws_obj = obj_att._get_work_schedule(contract_id=contract_id, check_in_date=new_date)['work_sched_obj']
            if ws_obj:
                return ws_obj.get_do_from_work_sched(date)
            else:
                return False

    def _get_leave(self, date):
        data = {
            'half_day': False,
            'absent': False,
            'sl': False,
            'vl': False
        }
        sl = self.env.ref('ph_payroll_leave.leave_type_sick', None).id
        vl = self.env.ref('ph_payroll_leave.leave_type_vacation', None).id

        obj_leave_date = self.env['hr.leave.date']
        args = [
            ('employee_id', '=', self.employee_id.id),
            ('payroll_period_id', '=', self.payroll_period_id.id),
            ('date', '=', date),
            ('approve', '=', True)
        ]
        leave_date = obj_leave_date.search(args, limit=1)
        if leave_date:
            leave_type = leave_date.leave_id.leave_allocation_id.holiday_status_id.leave_type
            leave_type_id = leave_date.leave_id.leave_allocation_id.holiday_status_id.id

            if not leave_date.leave_id.request_unit_half:
                if leave_type == 'unpaid':
                    data['absent'] = True
            else:
                data['half_day'] = True

            if leave_type_id == sl:
                data['sl'] = True
            elif leave_type_id == vl:
                data['vl'] = True
        return data

    def _get_ot(self):
        self.dtr_ot_ids = None
        obj_ot = self.env['hr.overtime']
        args = [
            ('payroll_period_id', '=', self.payroll_period_id.id),
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'approve')
        ]
        overtime = obj_ot.search(args)
        if overtime:
            for ot in overtime:
                self.dtr_ot_ids = [(0, 0, {'ot_id': ot.id})]

    def _get_ot_computations(self, computation_ids):
        comp = []
        for c in computation_ids:
            comp.append(c.computation_id.name)
        return ', '.join(comp)

    def _get_total_dtr(self):
        data = {
            'late': 0,
            'undertime': 0,
            'nd': 0
        }
        for line in self.dtr_line_ids:
            data['late'] += line.late
            data['undertime'] += line.undertime
            data['nd'] += line.nd
        return data

    def _get_total_ot(self):
        t_hrs = 0
        for ot in self.dtr_ot_ids:
            t_hrs += ot.ot_hours
        return t_hrs

    def float_time(self, value):
        hours, minutes = divmod(abs(value) * 60, 60)
        minutes = round(minutes)
        if minutes == 60:
            minutes = 0
            hours += 1
        if value < 0:
            return '-%02d:%02d' % (hours, minutes)
        return '%02d:%02d' % (hours, minutes)

    def _get_partner_address(self, p):
        obj_partner = self.env['res.partner']
        return obj_partner._get_partner_address(p)


class DailyTimeRecordLine(models.Model):
    _name = 'hr.employee.dtr.line'

    dtr_id = fields.Many2one('hr.employee.dtr', ondelete='cascade')
    date = fields.Date()
    sched_in = fields.Float(string='Sched. IN')
    time_in = fields.Datetime(string='Time IN')
    sched_out = fields.Float(string='Sched. OUT')
    time_out = fields.Datetime(string='Time OUT')
    late = fields.Float()
    undertime = fields.Float()
    half_day = fields.Boolean()
    absent = fields.Boolean()
    nd = fields.Float(string='ND')
    sl = fields.Boolean(string='SL')
    vl = fields.Boolean(string='VL')
    dayoff = fields.Boolean(string='DO', default=False)
    day_period = fields.Selection(DAY_PERIOD, required=False, default='morning')


class DailyTimeRecordOT(models.Model):
    _name = 'hr.employee.dtr.ot'

    dtr_id = fields.Many2one('hr.employee.dtr', ondelete='cascade')
    ot_id = fields.Many2one('hr.overtime')
    ot_fr = fields.Datetime(related='ot_id.ot_fr', string='From', store=True)
    ot_to = fields.Datetime(related='ot_id.ot_to', string='To')
    ot_hours = fields.Float(related='ot_id.ot_hours', string='Hours')
    # computation_id = fields.Many2one(related='ot_id.computation_id', model='hr.overtime.computation', string='Computation')
    computation_ids = fields.One2many(related='ot_id.computation_ids', model='hr.overtime.hours', string='Computations')
    notes = fields.Text(related='ot_id.notes', string='Remarks')


class AttendanceState(models.TransientModel):
    _name = 'attendance.state'

    @api.multi
    def _get_attendances(self):
        active_ids = self._context.get('active_ids')
        return [(6, 0, active_ids)]
    
    attendance_ids = fields.Many2many(comodel_name='hr.attendance', string='Attendances', default=_get_attendances)
    state = fields.Selection(STATE, default='draft')

    def change_state(self):
        obj_att = self.env['hr.attendance']
        if self.attendance_ids:
            for att in self.attendance_ids:
                if att.check_in and att.check_out:
                    att.state = self.state
                else:
                    check_in = check_out = None
                    if att.check_in:
                        check_in = (obj_att._localize_dt(att.check_in)).strftime('%m/%d/%Y %H:%M:%S')
                    if att.check_out:
                        check_out = (obj_att._localize_dt(att.check_out)).strftime('%m/%d/%Y %H:%M:%S')

                    raise ValidationError(_('Incomplete attendance\n\nEmployee: %s\nCheck In: %s\nCheck Out: %s' % (
                        att.employee_id.name, check_in, check_out)))
        else:
            raise ValidationError(_('Attendances must not be empty'))


class MultipleDTR(models.TransientModel):
    _name = 'multiple.dtr'

    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Employees', required=True)
    payroll_period_id = fields.Many2one('hr.payroll.period', string='Payroll Period', required=True)

    @api.multi
    def create_dtr(self):
        obj_dtr = self.env['hr.employee.dtr']
        if not self.employee_ids:
            raise ValidationError(_('Employees must not be empty'))

        for emp in self.employee_ids:
            vals = {
                'employee_id': emp.id,
                'payroll_period_id': self.payroll_period_id.id
            }
            new_dtr = obj_dtr.create(vals)
            new_dtr.get_dtr()


class MultipleAttendance(models.TransientModel):
    _name = 'multiple.attendance'

    check_in = fields.Datetime(required=True)
    check_out = fields.Datetime(required=True)
    memo = fields.Text()
    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Employees', required=True)

    def create_attendance(self):
        obj_att = self.env['hr.attendance']
        if not self.employee_ids:
            raise ValidationError(_('Employees must not be empty'))

        for emp in self.employee_ids:
            vals = {
                'employee_id': emp.id,
                'barcode': emp.barcode,
                'check_in': self.check_in,
                'check_out': self.check_out
            }
            new_att = obj_att.with_context(multi_att=True).create(vals)
            new_att.write({'memo': self.memo})


class Overtime(models.Model):
    _inherit = 'hr.overtime'

    attendance_ids = fields.One2many('hr.overtime.attendance', 'overtime_id')

    @api.onchange('ot_fr')
    def _get_attendance(self):
        if self.employee_id:
            if self.contract_id.wage_type == 'daily':
                self.attendance_ids = None
                obj_att = self.env['hr.attendance']
                fr = obj_att._localize_dt(self.ot_fr)
                localize_date = fields.Date.to_date(fr)

                # Use SQL SELECT to search attendance to avoid triggering _compute_worked_hours()
                qry = '''
                    SELECT id, late, undertime, overtime
                    FROM hr_attendance
                    WHERE employee_id = %s AND localize_date = %s
                    '''
                self.env.cr.execute(qry, [self.employee_id.id, localize_date])
                attendances = self.env.cr.fetchall()
                for att in attendances:
                    self.attendance_ids = [(0, 0, {
                            'attendance_id': att[0],
                            'late': att[1],
                            'undertime': att[2],
                            'overtime': att[3],
                        })]


class OvertimeAttendance(models.Model):
    _name = 'hr.overtime.attendance'

    overtime_id = fields.Many2one('hr.overtime', ondelete='cascade')
    attendance_id = fields.Many2one('hr.attendance')
    check_in = fields.Datetime(related='attendance_id.check_in')
    check_out = fields.Datetime(related='attendance_id.check_out')
    state = fields.Selection(related='attendance_id.state')
    late = fields.Float()
    undertime = fields.Float()
    overtime = fields.Float()


class OTRequestMulti(models.TransientModel):
    _name = 'ot.request.multi'

    @api.multi
    def _get_selected_attendances(self):
        active_ids = self._context.get('active_ids')
        return [(6, 0, active_ids)]

    payroll_period_id = fields.Many2one('hr.payroll.period', required=True)
    attendance_ids = fields.Many2many(comodel_name='hr.attendance', default=_get_selected_attendances)
    line_ids = fields.One2many('ot.request.multi.line', 'request_id')

    # def open_attendance_with_ot(self):
    #     view_id = self.env.ref('ph_payroll_attendance.new_attendance_tree').id
    #     domain = [
    #         ('payroll_period_id', '=', self.payroll_period_id.id),
    #         ('overtime', '>', 0),
    #         ('state', '=', 'validate')
    #     ]
    #     vals = {
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'tree',
    #         'view_mode': 'tree',
    #         'res_model': 'hr.attendance',
    #         'view_id': view_id,
    #         'target': 'new',
    #         'domain': domain
    #     }
    #     return vals


class OTRequestMultiLine(models.TransientModel):
    _name = 'ot.request.multi.line'
    _inherit = 'hr.overtime'

    request_id = fields.Many2one('ot.request.multi')
