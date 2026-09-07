from odoo import models, fields, api, _


class EmployeeContract(models.Model):
    _inherit = 'hr.contract'

    work_days = fields.Selection(selection_add=[('26days', '26 working days in a month')])

    @api.onchange('work_days', 'wage', 'daily_pay', 'cola_amount', 'factor_days')
    def compute_daily_monthly_rate(self):
        if self.wage_type == 'monthly':
            self.daily_pay = (self.wage * 12) / self.factor_days
        else:
            if self.work_days == '5wd':
                self.wage = (self.total_daily_pay * 261) / 12
            elif self.work_days == '6wd':
                self.wage = (self.total_daily_pay * 313) / 12
            elif self.work_days == '26days':
                self.wage = (self.total_daily_pay * 26)
