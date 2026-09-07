from odoo import models, fields, api, tools, _
from datetime import date


class Holiday(models.Model):
    _name = 'hr.holiday'
    _description = 'Holidays for the current year'
    _order = 'date desc'

    TYPE = [
        ('regular', 'Regular Holiday'),
        ('special', 'Special Holiday')
    ]

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    holiday_type = fields.Selection(TYPE, string='Type', default='regular', required=True)
    date = fields.Date(required=True, default=lambda *d: date.today())
    note = fields.Text()
    double_holiday = fields.Boolean()
    exempted_emp_ids = fields.Many2many(comodel_name='hr.employee', string='Exempted Employees')


class HolidayRate(models.Model):
    _name = 'hr.holiday.rate'

    TYPE = [
        ('regular', 'Regular/Legal Holiday'),
        ('special', 'Special Holiday'),
        ('double', 'Double Holiday')
    ]
    
    @api.multi
    def name_get(self):
        res = super(HolidayRate, self).name_get()
        for obj in self:
            name = [v for k, v in self.TYPE if k == obj.holiday_type][0]
            res.append((obj.id, name))
        return res

    holiday_type = fields.Selection(TYPE, string='Type', default='regular', required=True)
    holiday_rate = fields.Float(string='Holiday Rate', digits=(12,4), required=True)
    holiday_nd_rate = fields.Float(string='Holiday ND Rate', digits=(12,4), required=True)
