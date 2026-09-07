from odoo import fields, models, api


class HrOvertimeYYY(models.Model):
    _name = 'hr.overtime'
    _inherit = ['hr.overtime','mail.thread']
