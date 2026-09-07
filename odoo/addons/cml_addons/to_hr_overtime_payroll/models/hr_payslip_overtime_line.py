from odoo import models, fields, api


class HrPayslipOvertimeLine(models.Model):
    _name = 'hr.payslip.overtime.line'
    _description = 'Payslip Overtime Line'

    payslip_id = fields.Many2one('hr.payslip', string='Pay Slip', ondelete='cascade', index=True, required=True)
    contract_id = fields.Many2one('hr.contract', string='Contract', related="payslip_id.contract_id", store=True, index=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', related="payslip_id.employee_id", store=True, index=True)
    overtime_line_ids = fields.One2many('hr.overtime.line', 'payslip_ot_line_id', string='Overtime Details', compute='_compute_overtime_line_ids', store=True)
    number_of_hours = fields.Float(string='Number of Hours', compute='_compute_days_and_hours', store=True)
    number_of_days = fields.Float(string='Number of Days', compute='_compute_days_and_hours', store=True)
    rate = fields.Float(string="Rate(%)", compute='_compute_days_and_hours', store=True)
    overtime_rule_id = fields.Many2one('hr.overtime.rule', string='Overtime Rule', index=True, required=True)
    work_day_type_id = fields.Many2one('work.day.type', string='Work Day Type', index=True)
    code = fields.Char(string='Code', size=52, related='overtime_rule_id.code', store=True, index=True, readonly=True)

    @api.depends('payslip_id', 'payslip_id.hr_overtime_line_ids')
    def _compute_overtime_line_ids(self):
        for r in self:
            hr_overtime_line_ids = r.payslip_id.hr_overtime_line_ids.filtered(lambda line: line.overtime_rule_id.id == r.overtime_rule_id.id \
                                                                              and line.work_day_type_id == r.work_day_type_id)
            if hr_overtime_line_ids:
                r.overtime_line_ids = [(6, 0, hr_overtime_line_ids.ids)]
            else:
                r.overtime_line_ids = [(5)]

    @api.depends('overtime_line_ids')
    def _compute_days_and_hours(self):
        for r in self:
            overtime_line_ids = r.overtime_line_ids

            number_of_hours = 0
            number_of_days = 0
            l = len(overtime_line_ids)
            rate = 0

            last_local_datetime = False
            for i, overtime_line in enumerate(overtime_line_ids):
                rate = overtime_line.rate
                local_datetime = fields.Datetime.context_timestamp(r, fields.Datetime.from_string(overtime_line.start_time))

                if overtime_line.worked_hours > 0:
                    number_of_hours += overtime_line.worked_hours
                    if i == 0:
                        number_of_days += 1
                    elif i <= l - 1:

                        if local_datetime.date != last_local_datetime.date:
                            number_of_days += 1

                last_local_datetime = local_datetime

            r.number_of_hours = number_of_hours
            r.number_of_days = number_of_days
            r.rate = rate

