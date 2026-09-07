from odoo import models, api


class Payslip(models.Model):
    _inherit = 'hr.payslip'

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

                    data['other_earn'] += (self.paid_leave * self.daily_pay)

                elif col == '3':
                    data['deduct'] = slip.wtax + slip.sss_ee + slip.sss_ee_mpf + slip.phic_ee + slip.hdmf_ee + \
                        slip.late_amount + slip.undertime_amount #+ slip.halfday_amount

                else:
                    for ss in slip.slip_structure_ids.filtered(
                        lambda s: s.adjustment_id.adjustment_type in ('cashadvance', 'loan', 'otherdeduct') and s.active):
                        data['other_deduct'] += ss.amount
            return data
