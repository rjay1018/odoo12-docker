from odoo import models, api


class PayrollRegister(models.Model):
    _inherit = 'hr.payslip.run'

    def _payroll_summ_total(self):
        data = {
            'wage': 0,
            'daily_pay': 0,
            'basic_pay': 0,
            'regular_holiday_amount': 0,
            'cola_amount': 0,
            'unpaid_leave_amount': 0,
            'late_amount': 0,
            'undertime_amount': 0,
            'overtime_amount': 0,
            'night_diff_amount': 0,
            'total_premium': 0,
            'gross_pay': 0,
            'wtax': 0,
            'other_earning': 0,
            'other_deduction': 0,
            'net_pay': 0,
            'hdmf_ee': 0,
            'hdmf_er': 0,
            'phic_ee': 0,
            'phic_er': 0,
            'sss_ee': 0,
            'sss_ee_mpf': 0,
            'sss_er': 0,
            'sss_er_mpf': 0,
            'month_13th': 0,
            'vacation_leave_amount': 0,
            'sick_leave_amount': 0,
            'halfday_amount': 0,
            'absent_amount': 0
        }

        for slip in self.slip_ids.filtered(lambda s: not s.credit_note and s.state not in ('cancel', 'refund')):
            data['wage'] += slip.wage
            data['daily_pay'] += slip.daily_pay
            data['basic_pay'] += slip.basic_pay
            data['regular_holiday_amount'] += slip.regular_holiday_amount
            data['cola_amount'] += slip.cola_amount
            data['unpaid_leave_amount'] += slip.unpaid_leave_amount
            data['late_amount'] += slip.late_amount
            data['undertime_amount'] += slip.undertime_amount
            data['overtime_amount'] += slip.overtime_amount
            data['night_diff_amount'] += slip.night_diff_amount
            data['total_premium'] += slip.total_premium
            data['gross_pay'] += slip.gross_pay
            data['wtax'] += slip.wtax
            data['other_earning'] += slip.other_earning
            data['other_deduction'] += slip.other_deduction
            data['net_pay'] += slip.net_pay
            data['hdmf_ee'] += slip.hdmf_ee
            data['hdmf_er'] += slip.hdmf_er
            data['phic_ee'] += slip.phic_ee
            data['phic_er'] += slip.phic_er
            data['sss_ee'] += slip.sss_ee
            data['sss_ee_mpf'] += slip.sss_ee_mpf
            data['sss_er'] += slip.sss_er
            data['sss_er_mpf'] += slip.sss_er_mpf
            data['month_13th'] += slip.month_13th
            data['vacation_leave_amount'] += slip.vacation_leave_amount
            data['sick_leave_amount'] += slip.sick_leave_amount
            data['halfday_amount'] += slip.halfday_amount
            data['absent_amount'] += slip.absent_amount
        return data


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    def _get_ot_summary(self):
        for slip in self:
            data = {
                'reg_hrs': 0,
                'reg_hrs_amt': 0,
                
                'dayoff_hrs': 0,
                'dayoff_hrs_amt': 0,
                'dayoff_ot_hrs': 0,
                'dayoff_ot_hrs_amt': 0,

                'spc_hol_hrs': 0,
                'spc_hol_hrs_amt': 0,
                'spc_hol_ot_hrs': 0,
                'spc_hol_ot_hrs_amt': 0,
                'spc_hol_dayoff_hrs': 0,
                'spc_hol_dayoff_hrs_amt': 0,
                'spc_hol_dayoff_ot_hrs': 0,
                'spc_hol_dayoff_ot_hrs_amt': 0,

                'leg_hol_hrs': 0,
                'leg_hol_hrs_amt': 0,
                'leg_hol_ot_hrs': 0,
                'leg_hol_ot_hrs_amt': 0,
                'leg_hol_dayoff_hrs': 0,
                'leg_hol_dayoff_hrs_amt': 0,
                'leg_hol_dayoff_ot_hrs': 0,
                'leg_hol_dayoff_ot_hrs_amt': 0,

                'double_hol_hrs': 0,
                'double_hol_hrs_amt': 0,
                'double_hol_ot_hrs': 0,
                'double_hol_ot_hrs_amt': 0,
                'double_hol_dayoff_hrs': 0,
                'double_hol_dayoff_hrs_amt': 0,
                'double_hol_dayoff_ot_hrs': 0,
                'double_hol_dayoff_ot_hrs_amt': 0,
            }
            for ot in slip.overtime_summary_ids:
                # Regular
                if ot.ot_type == 'regular_ot':
                    data['reg_hrs'] += ot.ot_hours
                    data['reg_hrs_amt'] += ot.ot_amount

                # Day-Off/Rest Day
                elif ot.ot_type == 'dayoff':
                    data['dayoff_hrs'] += ot.ot_hours
                    data['dayoff_hrs_amt'] += ot.ot_amount
                elif ot.ot_type == 'dayoff_ot':
                    data['dayoff_ot_hrs'] += ot.ot_hours
                    data['dayoff_ot_hrs_amt'] += ot.ot_amount

                # Special Holiday
                elif ot.ot_type == 'spc_hol':
                    data['spc_hol_hrs'] += ot.ot_hours
                    data['spc_hol_hrs_amt'] += ot.ot_amount
                elif ot.ot_type == 'spc_hol_ot':
                    data['spc_hol_ot_hrs'] += ot.ot_hours
                    data['spc_hol_ot_hrs_amt'] += ot.ot_amount
                elif ot.ot_type == 'spc_hol_dayoff':
                    data['spc_hol_dayoff_hrs'] += ot.ot_hours
                    data['spc_hol_dayoff_hrs_amt'] += ot.ot_amount
                elif ot.ot_type == 'spc_hol_dayoff_ot':
                    data['spc_hol_dayoff_ot_hrs'] += ot.ot_hours
                    data['spc_hol_dayoff_ot_hrs_amt'] += ot.ot_amount

                # Regular/Legal Holiday
                elif ot.ot_type == 'leg_hol':
                    data['leg_hol_hrs'] += ot.ot_hours
                    data['leg_hol_hrs_amt'] += ot.ot_amount
                elif ot.ot_type == 'leg_hol_ot':
                    data['leg_hol_ot_hrs'] += ot.ot_hours
                    data['leg_hol_ot_hrs_amt'] += ot.ot_amount
                elif ot.ot_type == 'leg_hol_dayoff':
                    data['leg_hol_dayoff_hrs'] += ot.ot_hours
                    data['leg_hol_dayoff_hrs_amt'] += ot.ot_amount
                elif ot.ot_type == 'leg_hol_dayoff_ot':
                    data['leg_hol_dayoff_ot_hrs'] += ot.ot_hours
                    data['leg_hol_dayoff_ot_hrs_amt'] += ot.ot_amount

                # Double Holiday
                elif ot.ot_type == 'double_hol':
                    data['double_hol_hrs'] += ot.ot_hours
                    data['double_hol_hrs_amt'] += ot.ot_amount
                elif ot.ot_type == 'double_hol_ot':
                    data['double_hol_ot_hrs'] += ot.ot_hours
                    data['double_hol_ot_hrs_amt'] += ot.ot_amount
                elif ot.ot_type == 'double_hol_dayoff':
                    data['double_hol_dayoff_hrs'] += ot.ot_hours
                    data['double_hol_dayoff_hrs_amt'] += ot.ot_amount
                elif ot.ot_type == 'double_hol_dayoff_ot':
                    data['double_hol_dayoff_ot_hrs'] += ot.ot_hours
                    data['double_hol_dayoff_ot_hrs_amt'] += ot.ot_amount

            return data

    @api.multi
    def _get_slip_total(self, col=''):
        for slip in self:
            data = {
                'earn': 0,
                'other_earn': 0,
                'deduct': 0,
                'other_deduct': 0
            }

            if col:
                if col == '1':
                    data['earn'] = slip.basic_pay + slip.cola_amount + slip.night_diff_amount + slip.overtime_amount + slip.regular_holiday_amount

                elif col == '2':                    
                    for ss in slip.slip_structure_ids.filtered(
                        lambda s: s.adjustment_id.adjustment_type in ('allowance', 'otherbenefit', 'otherearning', 'refund', '13th_mo', '14th_mo') and s.active):
                        data['other_earn'] += ss.amount

                elif col == '3':
                    data['deduct'] = slip.wtax + slip.sss_ee + slip.sss_ee_mpf + slip.phic_ee + slip.hdmf_ee + \
                        slip.late_amount + slip.undertime_amount #+ slip.halfday_amount

                else:
                    for ss in slip.slip_structure_ids.filtered(
                        lambda s: s.adjustment_id.adjustment_type in ('cashadvance', 'loan', 'otherdeduct') and s.active):
                        data['other_deduct'] += ss.amount
            return data

    def _get_pay_master(self):
        obj_emp = self.env['hr.employee']
        pay_master = obj_emp.search([('payroll_master', '!=', False)], limit=1)
        if pay_master:
            return pay_master.name
        else:
            return '-'
