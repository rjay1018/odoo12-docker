from odoo import models, fields, api, tools, _
from odoo.addons.base.models.res_partner import _tz_get
from odoo.exceptions import ValidationError, UserError

from datetime import date


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    STATE = [
        ('draft', 'Draft'),
        ('approve', 'Approved'),
        ('cancel', 'Cancelled')
    ]

    @api.model
    def default_get(self, fields):
        res = super(ResourceCalendar, self).default_get(fields)
        if not res.get('name') and res.get('company_id'):
            res['name'] = ''
        return res

    def _get_default_attendance_ids(self):
        return [
            (0, 0, {'name': _('Monday'), 'dayofweek': '0', 'day_period': 'morning', 'hour_from': 8, 'hour_to': 17}),
            (0, 0, {'name': _('Tuesday'), 'dayofweek': '1', 'day_period': 'morning', 'hour_from': 8, 'hour_to': 17}),
            (0, 0, {'name': _('Wednesday'), 'dayofweek': '2', 'day_period': 'morning', 'hour_from': 8, 'hour_to': 17}),
            (0, 0, {'name': _('Thursday'), 'dayofweek': '3', 'day_period': 'morning', 'hour_from': 8, 'hour_to': 17}),
            (0, 0, {'name': _('Friday'), 'dayofweek': '4', 'day_period': 'morning', 'hour_from': 8, 'hour_to': 17}),
            (0, 0, {'name': _('Saturday'), 'dayofweek': '5', 'day_period': 'morning', 'hour_from': 8, 'hour_to': 17}),
            (0, 0, {'name': _('Sunday'), 'dayofweek': '6', 'day_period': 'morning', 'hour_from': 8, 'hour_to': 17})
        ]

    grace_period = fields.Float(default=0.0833333333333333, string='Grace Period (HH:MM)')
    work_break = fields.Float(default=0.0, string='Work Break (HH:MM)')
    regular_schedule = fields.Boolean()
    attendance_ids = fields.One2many('resource.calendar.attendance', 'calendar_id', 'Working Time', 
        copy=True, default=_get_default_attendance_ids)
    tz = fields.Selection(_tz_get, string='Timezone', required=True, default='Asia/Manila',
        help="This field is used in order to define in which timezone the resources will work.")
    state = fields.Selection(STATE, default='draft')
    short_name = fields.Char(required=False)

    @api.onchange('regular_schedule')
    def onchange_break(self):
        self.work_break = 0
        self.attendance_ids = None
        if self.regular_schedule:
            self.work_break = 1.0

            self.attendance_ids = [
                (0, 0, {'name': _('Monday'), 'dayofweek': '0', 'day_period': 'morning', 'hour_from': 8, 'hour_to': 12}),
                (0, 0, {'name': _('Monday'), 'dayofweek': '0', 'day_period': 'afternoon', 'hour_from': 13, 'hour_to': 17}),
                (0, 0, {'name': _('Tuesday'), 'dayofweek': '1', 'day_period': 'morning', 'hour_from': 8, 'hour_to': 12}),
                (0, 0, {'name': _('Tuesday'), 'dayofweek': '1', 'day_period': 'afternoon', 'hour_from': 13, 'hour_to': 17}),
                (0, 0, {'name': _('Wednesday'), 'dayofweek': '2', 'day_period': 'morning', 'hour_from': 8, 'hour_to': 12}),
                (0, 0, {'name': _('Wednesday'), 'dayofweek': '2', 'day_period': 'afternoon', 'hour_from': 13, 'hour_to': 17}),
                (0, 0, {'name': _('Thursday'), 'dayofweek': '3', 'day_period': 'morning', 'hour_from': 8, 'hour_to': 12}),
                (0, 0, {'name': _('Thursday'), 'dayofweek': '3', 'day_period': 'afternoon', 'hour_from': 13, 'hour_to': 17}),
                (0, 0, {'name': _('Friday'), 'dayofweek': '4', 'day_period': 'morning', 'hour_from': 8, 'hour_to': 12}),
                (0, 0, {'name': _('Friday'), 'dayofweek': '4', 'day_period': 'afternoon', 'hour_from': 13, 'hour_to': 17}),
                (0, 0, {'name': _('Saturday'), 'dayofweek': '5', 'day_period': 'morning', 'hour_from': 8, 'hour_to': 12}),
                (0, 0, {'name': _('Saturday'), 'dayofweek': '5', 'day_period': 'afternoon', 'hour_from': 13, 'hour_to': 17}),
                (0, 0, {'name': _('Sunday'), 'dayofweek': '6', 'day_period': 'morning', 'hour_from': 8, 'hour_to': 12}),
                (0, 0, {'name': _('Sunday'), 'dayofweek': '6', 'day_period': 'afternoon', 'hour_from': 13, 'hour_to': 17})
            ]
        else:
            self.attendance_ids = self._get_default_attendance_ids()

    def action_approve(self):
        self.state = 'approve'

    def action_cancel(self):
        self.state = 'cancel'

    def action_draft(self):
        self.state = 'draft'

    def get_do_from_work_sched(self, date_obj):
        y, m, d = str(fields.Date.to_string(date_obj)).split('-')
        new_date = date(int(y), int(m), int(d))
        dow = str(new_date.weekday())
        is_do = bool(self.attendance_ids.filtered(lambda c: c.dayoff and c.dayofweek == dow))
        return is_do


class Resource(models.Model):
    _inherit = 'resource.resource'

    tz = fields.Selection(_tz_get, string='Timezone', required=True, default='Asia/Manila',
        help="This field is used in order to define in which timezone the resources will work.")


class ResourceCalendarAttendance(models.Model):
    _inherit = 'resource.calendar.attendance'
    _order = 'dayofweek, hour_from'

    DOW = [
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ]

    DAY_PERIOD = [
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon')
    ]

    day_period = fields.Selection(DAY_PERIOD, required=True, default='morning')
    hour_from = fields.Float(string='Work From', required=True, index=True)
    hour_to = fields.Float(string='Work To', required=True)
    has_nd = fields.Boolean('Has ND', default=False, help='Set to True if this schedule has night differential')
    dayoff = fields.Boolean('Day-Off/Rest-Day')

    @api.onchange('dayofweek')
    def onchange_dow(self):
        self.name = [v for k, v in self.DOW if k == self.dayofweek][0] or '-'

    @api.onchange('hour_from', 'hour_to')
    def _onchange_hours(self):
        # avoid negative or after midnight
        self.hour_from = min(self.hour_from, 23.99)
        self.hour_from = max(self.hour_from, 0.0)
        self.hour_to = min(self.hour_to, 23.99)
        self.hour_to = max(self.hour_to, 0.0)

        self.has_nd = False
        if self.hour_to > 22 or self.hour_to <= 6 or self.hour_from >= 22 or self.hour_from < 6:
            self.has_nd = True

        # avoid wrong order
        # Need to comment this line for graveyard shifting to work
        # self.hour_to = max(self.hour_to, self.hour_from)


class WorkScheduling(models.TransientModel):
    _name = 'work.scheduling'
    _rec_name = 'resource_calendar_id'

    resource_calendar_id = fields.Many2one('resource.calendar', string='Work Schedule', required=True)
    date_fr = fields.Date(string='Valid From', required=True)
    date_to = fields.Date(string='Valid To', required=True)
    employee_ids = fields.Many2many(comodel_name='hr.employee', required=True)

    @api.multi
    def apply_work_sched(self):
        obj_work_sched = self.env['hr.contract.work.schedule']
        obj_contract = self.env['hr.contract']

        if not self.employee_ids:
            raise ValidationError(_('Employees must not be empty'))

        for emp in self.employee_ids:
            contract_id = obj_contract.get_active_contract(emp)
            vals = {
                'contract_id': contract_id,
                'resource_calendar_id': self.resource_calendar_id.id,
                'date_fr': self.date_fr,
                'date_to': self.date_to
            }
            new_work_sched = obj_work_sched.create(vals)
            new_work_sched.contract_id.work_shift_fix = False
            new_work_sched.contract_id.resource_calendar_id = None
            new_work_sched.action_run()

        return {'type': 'ir.actions.act_window_close'}
