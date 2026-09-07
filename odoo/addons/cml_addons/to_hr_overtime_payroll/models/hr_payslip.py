from odoo import models, fields, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    hr_overtime_line_ids = fields.One2many('hr.overtime.line', 'payslip_id', string='Overtime Details', copy=False,
                                           compute='_compute_hr_overtime_line_ids', store=True)

    payslip_ot_line_ids = fields.One2many('hr.payslip.overtime.line', 'payslip_id', string='Payslip Overtime', compute='_compute_payslip_ot_line_ids',
                                          copy=False, store=True)

    @api.multi
    def action_payslip_done(self):
        self.mapped('hr_overtime_line_ids').action_done()
        return super(HrPayslip, self).action_payslip_done()

    @api.multi
    def action_payslip_cancel(self):
        self.mapped('hr_overtime_line_ids').action_re_approve()
        return super(HrPayslip, self).action_payslip_cancel()

    @api.depends('employee_id', 'contract_id', 'date_from', 'date_to')
    def _compute_hr_overtime_line_ids(self):
        OvertimeLine = self.env['hr.overtime.line']
        for r in self:
            if r.employee_id and r.date_from and r.date_to:
                domain = [
                    ('employee_id', '=', r.employee_id.id),
                    ('start_time', '>=', r.date_from),
                    ('end_time', '<=', r.date_to),
                    '|', ('payslip_id', '=', False), ('payslip_id', '=', r.id)
                    ]
                if r.contract_id:
                    domain = ['|', ('hr_contract_id', '=', False), ('hr_contract_id', '=', r.contract_id.id)] + domain

                hr_overtime_line_ids = OvertimeLine.search(domain)
                r.hr_overtime_line_ids = hr_overtime_line_ids.ids or False
            else:
                r.hr_overtime_line_ids = False

    def _prepare_payslip_ot_line_data(self, overtime_rule_id, work_day_type_id):
        return {
            'payslip_id': self.id,
            'overtime_rule_id': overtime_rule_id.id,
            'work_day_type_id': work_day_type_id and work_day_type_id.id or False
            }

    @api.depends('hr_overtime_line_ids')
    def _compute_payslip_ot_line_ids(self):
        for r in self:
            if not r.hr_overtime_line_ids:
                r.payslip_ot_line_ids = False
            else:
                data = []
                work_day_type_ids = r.hr_overtime_line_ids.mapped('work_day_type_id')
                for ot_rule_id in r.hr_overtime_line_ids.mapped('overtime_rule_id'):
                    for work_day_type_id in work_day_type_ids:
                        overtime_line_ids = r.hr_overtime_line_ids.filtered(lambda x: x.overtime_rule_id == ot_rule_id and x.work_day_type_id == work_day_type_id)
                        if overtime_line_ids:
                            data.append((0, 0, r._prepare_payslip_ot_line_data(ot_rule_id, work_day_type_id)))
                r.payslip_ot_line_ids = data

