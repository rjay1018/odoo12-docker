from odoo import models, fields, api
from odoo import tools


class HrOvertimeReport(models.Model):
    _name = 'hr.overtime.report'
    _description = "Overtime Report"
    _order = 'start_time desc'
    _auto = False

    start_time = fields.Datetime(string='Time From')
    end_time = fields.Datetime(string='Time To')
    create_date = fields.Datetime(string='Date Created')
    payslip_id = fields.Many2one('hr.payslip', string='Payslip', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True)
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    job_id = fields.Many2one('hr.job', string='Job Position', readonly=True)
    worked_hours = fields.Float(string='Worked Hours', readonly=True)
    hr_contract_id = fields.Many2one('hr.contract', string='Contract', readonly=True)
    overtime_rule_id = fields.Many2one('hr.overtime.rule', string="Rule", readonly=True)
    payslip_id = fields.Many2one('hr.payslip', string='Payslip', readonly=True)
    reason_id = fields.Many2one('hr.overtime.reason', string='Reason', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('canceled', 'Cancelled'),
        ('done', 'Done'),
        ], string='Status', readonly=True)
    work_day_type_id = fields.Many2one('work.day.type', string='Work Day Type', readonly=True)

    def _select(self):
        sql = """
        SELECT
            l.id AS id,
            l.worked_hours,
            l.employee_id,
            l.department_id,
            l.job_id,
            l.overtime_rule_id,
            l.state,
            l.hr_contract_id,
            l.start_time,
            l.end_time,
            l.create_date,
            ps.id AS payslip_id,
            res.id AS reason_id,
            wdt.id AS work_day_type_id
        """
        return sql

    def _from(self):
        sql = """
        FROM
            hr_overtime_line AS l
        """
        return sql

    def _join(self):
        sql = """
            LEFT JOIN hr_payslip_overtime_line AS psotl ON psotl.id = l.payslip_ot_line_id
            LEFT JOIN hr_payslip AS ps ON ps.id = psotl.payslip_id
            LEFT JOIN hr_overtime_reason AS res ON res.id = l.reason_id
            LEFT JOIN work_day_type AS wdt ON wdt.id = l.work_day_type_id
        """
        return sql

    def _where(self):
        sql = """
        WHERE
            l.state != 'draft'
        """
        return sql

    def _group_by(self):
        group_by_str = """
        """
        return group_by_str

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            %s
            %s
            %s
            %s
            )
        """ % (self._table, self._select(), self._from(), self._join(), self._where(), self._group_by()))

