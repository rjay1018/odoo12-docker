from odoo import api, fields, models
from odoo.tools.float_utils import float_compare


class ResourceCalendar(models.Model):
    _name = 'resource.calendar'
    _inherit = ['resource.calendar', 'to.base']

    @api.multi
    def get_attendances_for_date(self, day_dt):
        """ Given a datetime, return matching attendances """
        self.ensure_one()
        weekday = day_dt.weekday()
        float_time = self.time_to_float_hour(day_dt.time())

        attendances = self.env['resource.calendar.attendance']

        for attendance in self.attendance_ids.filtered(
            lambda att:
                int(att.dayofweek) == weekday and
                float_compare(att.hour_from, float_time, precision_digits=2) != 1 and
                float_compare(att.hour_to, float_time, precision_digits=2) != -1 and
                not (att.date_from and fields.Date.from_string(att.date_from) > day_dt.date()) and
                not (att.date_to and fields.Date.from_string(att.date_to) < day_dt.date())):
            attendances |= attendance
        return attendances

    @api.multi
    def is_overlaping(self, date_start, date_end):
        """
        Method to check if an interval sepecified by ot_date_start and ot_date_end is overlaping an attendance of the calendar
        :param date_start: the start date of the interval to check
        :param date_end: the end date of the interval to check
        :return bool, attendances:
        """
        self.ensure_one()
        attendances = self.env['resource.calendar.attendance']
        attendances |= self.get_attendances_for_date(date_start)
        attendances |= self.get_attendances_for_date(date_end)
        if attendances:
            return True, attendances
        return False, attendances

