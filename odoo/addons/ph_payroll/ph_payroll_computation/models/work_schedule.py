from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, datetime
import logging
_logger = logging.getLogger(__name__)


class WorkScheduleReport(models.TransientModel):
    _name = 'work.schedule.report'

    TYPE = [
        ('employee', 'Employee'),
        ('department', 'Department'),
        ('all', 'All')
    ]

    report_type = fields.Selection(TYPE, required=True, default='all')
    payroll_period_id = fields.Many2one('hr.payroll.period', string='Payroll Period', required=True)
    department_id = fields.Many2one('hr.department', string='Department')
    employee_ids = fields.Many2many(comodel_name='hr.employee')

    @api.onchange('department_id')
    def onchange_department(self):
        domain = []
        self.employee_ids = None
        if self.department_id:
            domain.extend([('department_id', '=', self.department_id.id)])

        return {'domain': {'employee_ids': domain}}

    def _get_company_address(self):
        addr_list = []
        partner = self.env.user.company_id.partner_id
        
        addr_list.append((partner.street).strip() if partner.street else '')
        addr_list.append((partner.street2).strip() if partner.street2 else '')
        addr_list.append((partner.city).strip() if partner.city else '')
        addr_list.append((partner.state_id.name).strip() if partner.state_id else None)
        addr_list.append((partner.zip).strip() if partner.zip else '')
        addr_list.append((partner.country_id.name).strip() if partner.country_id else None)

        addr = filter(None, addr_list)
        return ', '.join(addr)

    def _get_payroll_period_dates(self):
        obj_pay_date = self.env['hr.payroll.period.date']
        pay_dates = obj_pay_date.search([('payroll_period_id', '=', self.payroll_period_id.id)], order='date')
        return pay_dates

    def _parse_work_sched_dates(self, fr, to):
        date_list = []
        for date in self.env['hr.leave']._parse_dates(fr, to):
            date_list.append(fields.Date.to_string(date))
        return date_list

    def _get_working_hours(self, employee):
        work_scheds = []
        worked_hours = []
        payroll_period_dates = []

        contract = self.env['hr.contract'].get_active_contract(employee, False, True)
        if contract:
            payroll_period_dates = [p.date for p in self._get_payroll_period_dates()]

            dayoff_dates = []
            dayoff_dates = [fields.Date.to_string(do.day_off_date) for do in self._get_dayoff(employee.id)]

            ws_dates_dict = {}
            scheds = self._get_period_work_sched(employee.id)
            for sched in scheds:
                for pd in self._parse_work_sched_dates(sched.date_fr, sched.date_to):
                    ws_dates_dict[pd] = sched.resource_calendar_id.short_name

                for k, v in ws_dates_dict.items():
                    work_scheds.append(k)

            for pp_date in payroll_period_dates:
                ppd = fields.Date.to_string(pp_date)
                ws_dates = work_scheds
                if ppd in ws_dates:
                    if ppd not in dayoff_dates:
                        wh = self._get_dayoff_from_work_sched(contract.id, pp_date)
                        if wh == '-':
                            sched_name = [v for k, v in ws_dates_dict.items() if k == ppd]
                            if sched_name:
                                worked_hours.append(sched_name[0])
                        else:
                            worked_hours.append(wh)
                    else:
                        worked_hours.append('DO')

                else:
                    # Check if Fix Schedule
                    if contract:
                        if contract.work_shift_fix and contract.resource_calendar_id:
                            if ppd not in dayoff_dates:
                                wh = self._get_dayoff_from_work_sched(contract.id, pp_date)
                                if wh == '-':
                                    worked_hours.append(contract.resource_calendar_id.short_name)
                                else:
                                    worked_hours.append(wh)
                            else:
                                worked_hours.append('DO')
                        else:
                            worked_hours.append('-')
                    else:
                        worked_hours.append('-')
        return worked_hours

    def _get_dayoff(self, employee_id):
        obj_dayoff = self.env['hr.dayoff.calendar']
        args = [
            ('payroll_period_id', '=', self.payroll_period_id.id),
            ('employee_id', '=', employee_id)
        ]
        return obj_dayoff.search(args)

    def _get_dayoff_from_work_sched(self, contract_id, date):
        obj_att = self.env['hr.attendance']
        str_date = str(date) + ' 00:00:00'
        new_date = fields.Datetime.to_datetime(str_date)
        ws_obj = obj_att._get_work_schedule(contract_id=contract_id, check_in_date=new_date)['work_sched_obj']
        if ws_obj:
            if ws_obj.get_do_from_work_sched(date):
               return 'DO'
            else:
                return '-' 
        else:
            return '-'

    def _parse_dates(self, fr, to):
        obj_leave = self.env['hr.leave']
        return obj_leave._parse_dates(fr, to)

    def _get_period_work_sched(self, employee_id):
        date_fr = fields.Date.to_string(self.payroll_period_id.period_fr)
        date_to = fields.Date.to_string(self.payroll_period_id.period_to)
        clause_1 = ['&', ('date_to', '<=', date_to), ('date_to', '>=', date_fr)]
        clause_2 = ['&', ('date_fr', '<=', date_to), ('date_fr', '>=', date_fr)]
        clause_3 = ['&', ('date_fr', '<=', date_fr), '|', ('date_to', '=', False), ('date_to', '>=', date_to)]
        clause_final = [('employee_id', '=', employee_id), ('state', '=', 'open'), '|', '|'] + clause_1 + clause_2 + clause_3        
        return self.env['hr.contract.work.schedule'].search(clause_final, order='date_fr')

    @api.multi
    def print_report(self):
        return self.env.ref('ph_payroll_computation.work_sched_document_rpt_id').report_action(self)
