from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.osv import expression


class HrOvertimeRule(models.Model):
    _name = 'hr.overtime.rule'
    _inherit = ['mail.thread', 'to.base']
    _order = 'dayofweek ASC, hour_from ASC'

    DOW = [
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
        ('-1', 'Holiday'),
        ('-2', 'Holiday on SAT'),
        ('-3', 'Holiday on SUN')]

    name = fields.Char(string='Name', required=True, translate=True, track_visibility='onchange')
    dayofweek = fields.Selection(DOW, string='Day of Week', required=True, index=True, track_visibility='onchange')
    hour_from = fields.Float(string='Work From', track_visibility='onchange',
                             required=True,
                             help='Start and End time of overtime working.',
                             index=True)
    hour_to = fields.Float(string='Work To', track_visibility='onchange',
                           required=True)
    code_id = fields.Many2one('hr.overtime.rule.code', required=True, track_visibility='onchange', string='Rule Code',
                              help='The predefined code to be used in overtime payroll computation')

    code = fields.Char(string='Code', related='code_id.name', readonly=True)
    rate = fields.Float(related='code_id.rate', readonly=True, track_visibility='onchange')

    company_id = fields.Many2one('res.company', string='Company', track_visibility='onchange',
                                 default=lambda self: self.env.user.company_id,
                                 help='If a company is set, this rule will be valid for that company only')

    _sql_constraints = [
        ('date_check', "CHECK (hour_from < hour_to)", "The Work From must be anterior to the Work To."),
    ]

    @api.multi
    def name_get(self):
        return [(rule.id, '%s%s (%s - %s)' % ('[%s] ' % rule.code, rule.name, rule.hours_time_string(rule.hour_from), rule.hours_time_string(rule.hour_to)))
                for rule in self]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """
        name search that supports searching by rule and code and times
        """
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&'] + domain
        rules = self.search(domain + args, limit=limit)
        return rules.name_get()

    @api.constrains('dayofweek', 'hour_from', 'hour_to', 'company_id')
    def _overlapping_check(self):
        for r in self:
            overlap = self.search([
                ('id', '!=', r.id),
                ('dayofweek', '=', r.dayofweek),
                ('hour_from', '<', r.hour_to),
                ('hour_to', '>', r.hour_from),
                '|',
                ('company_id', '=', r.company_id.id),
                ('company_id', '=', False)
                ], limit=1)
            if overlap:
                raise UserError(_("You have entered an interval that is overlapping the interval of an existing rule (%s)!")
                                % (overlap.name,))

    @api.model
    def get_by_datetime(self, dt, is_holiday, start_date=True):
        """
        Search overtime rule by the input datetime and is_holiday flag
        :param dt: the start date or end_date of an overtime period (depending on the arg start_date)
        :param is_holiday
        :param start_date: boolean field to indicate if the passed dt is either start date or end date of an overtime period 
        """
        weekday = dt.weekday()
        if is_holiday:
            if weekday == 5:
                weekday = '-2'
            elif weekday == 6:
                weekday = '-3'
            else:
                weekday = '-1'
        float_hours = self.time_to_float_hour(dt.time())
        if start_date:
            order = 'hour_from DESC'
        else:
            order = 'hour_from ASC'
        return self.search([('dayofweek', '=', weekday), ('hour_from', '<=', float_hours), ('hour_to', '>=', float_hours)], limit=1, order=order)

    @api.model
    def is_crossing(self, dt_start, dt_end, is_holiday):
        """
        This method is to check if an interval combined by dt_start and dt_end
        is crossing more than one rule
        :param dt_start: the start date of the interval in datetime type
        :param dt_end: the start date of the interval in datetime type

        :return bool, first_match, second_match:
        """
        first_match = self.get_by_datetime(dt_start, is_holiday, start_date=True)
        second_match = self.get_by_datetime(dt_end, is_holiday, start_date=False)
        if first_match and second_match and first_match != second_match:
            return True, first_match, second_match
        return False, first_match, second_match

