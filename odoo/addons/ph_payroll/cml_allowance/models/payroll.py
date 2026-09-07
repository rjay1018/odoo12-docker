from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    def _get_worked_hours(self):
        att = self._get_attendance()
        ps = self._compute_pass_slip()
        undertime = (att['undertime'] + ps['personal']) - ps['official']
        return (att['work_days'] * 8) - undertime

    def _compute_contract(self):
        res = super(Payslip, self)._compute_contract()
        adj_pa_id = self.env.ref('cml_allowance.adj_personal_allow').id
        self.slip_structure_ids.filtered(lambda a: a.adjustment_id.id == adj_pa_id).unlink()
        for s in self.contract_id.structure_ids.filtered(lambda a: a.state == 'open' and a.adjustment_id.id == adj_pa_id):
            if s.period_type == self.payroll_period_id.period_type or s.period_type == '1st_2nd':
                vals = {
                    'structure_line_id': s.id,
                    'adjustment_id': s.adjustment_id.id,
                    'amount': self._get_worked_hours() * s.amount
                }
                self.slip_structure_ids = [(0, 0, vals)]
        return res
