from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError


class LateDeduction(models.Model):
    _name = 'hr.late.deduction.table'
    _description = 'Late Deduction Table'

    min_fr = fields.Float('From', required=True)
    min_to = fields.Float('To', required=True)
    late = fields.Float('Late', required=True)

    @api.onchange('min_to')
    def onchange_min_to(self):
        self.late = self.min_to


class PremiumsTaxConfig(models.Model):
    _inherit = 'hr.premiums.tax.config'

    CONSO_PERIOD = [
        ('1st', '1st Half'),
        ('2nd', '2nd Half')
    ]

    sss_consolidate = fields.Boolean('Consolidate')
    sss_consolidate_period = fields.Selection(CONSO_PERIOD, string='In Period Type')

    @api.onchange('period_type')
    def onchange_period_type(self):
        if self.period_type != '1st_2nd':
            self.sss_consolidate = False
            self.sss_consolidate_period = None

    @api.onchange('sss_consolidate')
    def onchange_consolidate(self):
        if not self.sss_consolidate:
            self.sss_consolidate_period = None


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    def _get_previous_slip_data(self):
        obj_slip = self.env['hr.payslip']
        prev_pay_period = self.env['hr.payroll.period']._get_previous_period(self.payroll_schedule, self.payroll_period_id)
        args = [
            ('employee_id', '=', self.employee_id.id),
            ('payroll_period_id', '=', prev_pay_period.id),
            ('state', 'not in', ('cancel', 'refund')),
            ('credit_note', '=', False)
        ]
        slip = obj_slip.search(args, limit=1)
        return slip

    def _get_basic_pay(self):
        basic_pay = 0
        if self.contract_id.has_attendance:
            if self.wage_type == 'daily':
                basic_pay = self.daily_pay * self.work_days

                # Put paid leave under Other Earnings
                # basic_pay += self.daily_pay * self.paid_leave
            else:
                if self.payroll_schedule == '1_d':
                    basic_pay = self.daily_pay * 7
                elif self.payroll_schedule == '2_w':
                    basic_pay = self.wage / 4
                elif self.payroll_schedule == '3_sm':
                    basic_pay = self.wage / 2
                elif self.payroll_schedule == '4_m':
                    basic_pay = self.wage
        else:
            if self.payroll_schedule == '1_d':
                basic_pay = self.wage / 7
            elif self.payroll_schedule == '2_w':
                basic_pay = self.wage / 4
            elif self.payroll_schedule == '3_sm':
                basic_pay = self.wage / 2
            elif self.payroll_schedule == '4_m':
                basic_pay = self.wage
        return basic_pay + self._get_basic_pay_adjustment()

    @api.one
    @api.depends('contract_id')
    def _compute_premiums(self):
        self.ensure_one()
        obj_hdmf = self.env['hdmf.table']
        obj_phic = self.env['phic.table']
        obj_sss = self.env['sss.table']
        obj_prem_tax_config = self.env['hr.premiums.tax.config']

        if not self.journal_id:
            self.journal_id = self._get_salary_journal()

        self.hdmf_ee = self.hdmf_er = 0
        self.phic_ee = self.phic_er = 0
        self.sss_ee = self.sss_er = 0
        self.sss_ee_mpf = self.sss_er_mpf = 0

        base_wage = self.wage

        hdmf_period_type = obj_prem_tax_config._get_premium_tax_data('hdmf').period_type
        phic_period_type = obj_prem_tax_config._get_premium_tax_data('phic').period_type

        sss_data = obj_prem_tax_config._get_premium_tax_data('sss')
        sss_period_type = sss_data.period_type
        sss_conso = sss_data.sss_consolidate
        sss_conso_period = sss_data.sss_consolidate_period

        prev_slip = self._get_previous_slip_data()

        work_days = self.contract_id.work_days
        if work_days == '26days':
            basic_pay = self._get_basic_pay()
            wage_26days_hdmf = wage_26days_phic = wage_26days_sss = basic_pay
            wage_26days_total = basic_pay + prev_slip.basic_pay

            if hdmf_period_type != '1st_2nd':
                wage_26days_hdmf = wage_26days_total
            if phic_period_type != '1st_2nd':
                wage_26days_phic = wage_26days_total
            if sss_period_type != '1st_2nd' or (sss_conso and sss_conso_period):
                wage_26days_sss = wage_26days_total

            hdmf_ee = obj_hdmf._get_hdmf(wage_26days_hdmf)['ee']
            hdmf_er = obj_hdmf._get_hdmf(wage_26days_hdmf)['er']
            phic_ee = obj_phic._get_phic(wage_26days_phic)['ee']
            phic_er = obj_phic._get_phic(wage_26days_phic)['er']
            sss_ee = obj_sss._get_sss(wage_26days_sss)['ee']
            sss_er = obj_sss._get_sss(wage_26days_sss)['er']
            sss_ee_mpf = obj_sss._get_sss(wage_26days_sss)['mpf_ee']
            sss_er_mpf = obj_sss._get_sss(wage_26days_sss)['mpf_er']
        else:
            hdmf_ee = obj_hdmf._get_hdmf(base_wage)['ee']
            hdmf_er = obj_hdmf._get_hdmf(base_wage)['er']
            phic_ee = obj_phic._get_phic(base_wage)['ee']
            phic_er = obj_phic._get_phic(base_wage)['er']
            sss_ee = obj_sss._get_sss(base_wage)['ee']
            sss_er = obj_sss._get_sss(base_wage)['er']
            sss_ee_mpf = obj_sss._get_sss(base_wage)['mpf_ee']
            sss_er_mpf = obj_sss._get_sss(base_wage)['mpf_er']

        payroll_period_type = self.payroll_period_id.period_type

        if work_days != '26days':
            if self.payroll_schedule == '2_w': # Weekly
                if self.contract_id.hdmf:
                    if self.contract_id.hdmf_amount == 0:
                        self.hdmf_ee = hdmf_ee / 4
                    else:
                        self.hdmf_ee = self.contract_id.hdmf_amount / 4
                    self.hdmf_er = hdmf_er / 4
                if self.contract_id.phic:
                    if self.contract_id.phic_amount == 0:
                        self.phic_ee = phic_ee / 4
                        self.phic_er = phic_er / 4
                    else:
                        self.phic_ee = self.contract_id.phic_amount / 4
                        self.phic_er = self.contract_id.phic_amount / 4
                if self.contract_id.sss:
                    if self.contract_id.sss_amount == 0:
                        self.sss_ee = sss_ee / 4
                        self.sss_ee_mpf = sss_ee_mpf / 4
                    else:
                        self.sss_ee = self.contract_id.sss_amount / 4
                    self.sss_er = sss_er / 4
                    self.sss_er_mpf = sss_er_mpf / 4

            elif self.payroll_schedule == '3_sm': # Semi-Monthly
                if self.contract_id.hdmf:
                    if self.contract_id.hdmf_amount == 0:
                        if hdmf_period_type == '1st_2nd':
                            self.hdmf_ee = hdmf_ee / 2
                            self.hdmf_er = hdmf_er / 2
                        else:
                            if hdmf_period_type == payroll_period_type:
                                self.hdmf_ee = hdmf_ee
                                self.hdmf_er = hdmf_er
                    else:
                        if hdmf_period_type == '1st_2nd':
                            self.hdmf_ee = self.contract_id.hdmf_amount / 2
                            self.hdmf_er = hdmf_er / 2
                        else:
                            if hdmf_period_type == payroll_period_type:
                                self.hdmf_ee = self.contract_id.hdmf_amount
                                self.hdmf_er = hdmf_er

                if self.contract_id.phic:
                    if self.contract_id.phic_amount == 0:
                        if phic_period_type == '1st_2nd':
                            self.phic_ee = phic_ee / 2
                            self.phic_er = phic_er / 2
                        else:
                            if phic_period_type == payroll_period_type:
                                self.phic_ee = phic_ee
                                self.phic_er = phic_er
                    else:
                        if phic_period_type == '1st_2nd':
                            self.phic_ee = self.contract_id.phic_amount / 2
                            self.phic_er = self.contract_id.phic_amount / 2
                        else:
                            if phic_period_type == payroll_period_type:
                                self.phic_ee = self.contract_id.phic_amount
                                self.phic_er = self.contract_id.phic_amount

                if self.contract_id.sss:
                    if self.contract_id.sss_amount == 0:
                        if sss_period_type == '1st_2nd':
                            self.sss_ee = sss_ee / 2
                            self.sss_er = sss_er / 2
                            self.sss_ee_mpf = sss_ee_mpf / 2
                            self.sss_er_mpf = sss_er_mpf / 2
                        else:
                            if sss_period_type == payroll_period_type:
                                self.sss_ee = sss_ee
                                self.sss_er = sss_er
                                self.sss_ee_mpf = sss_ee_mpf
                                self.sss_er_mpf = sss_er_mpf
                    else:
                        if sss_period_type == '1st_2nd':
                            self.sss_ee = self.contract_id.sss_amount / 2
                            self.sss_er = sss_er / 2
                            self.sss_ee_mpf = sss_ee_mpf / 2
                            self.sss_er_mpf = sss_er_mpf / 2
                        else:
                            if sss_period_type == payroll_period_type:
                                self.sss_ee = self.contract_id.sss_amount
                                self.sss_er = sss_er
                                self.sss_ee_mpf = sss_ee_mpf
                                self.sss_er_mpf = sss_er_mpf

            elif self.payroll_schedule == '4_m': # Monthly
                if self.contract_id.hdmf:
                    if self.contract_id.hdmf_amount == 0:
                        self.hdmf_ee = hdmf_ee
                    else:
                        self.hdmf_ee = self.contract_id.hdmf_amount
                    self.hdmf_er = hdmf_er
                if self.contract_id.phic:
                    if self.contract_id.phic_amount == 0:
                        self.phic_ee = phic_ee
                        self.phic_er = phic_er
                    else:
                        self.phic_ee = self.contract_id.phic_amount
                        self.phic_er = self.contract_id.phic_amount
                if self.contract_id.sss:
                    if self.contract_id.sss_amount == 0:
                        self.sss_ee = sss_ee
                        self.sss_ee_mpf = sss_ee_mpf
                    else:
                        self.sss_ee = self.contract_id.sss_amount
                    self.sss_er = sss_er
                    self.sss_er_mpf = sss_er_mpf
        else:
            # HDMF custom computation - 26 working days/month
            if self.contract_id.hdmf:
                if hdmf_period_type == payroll_period_type or hdmf_period_type == '1st_2nd':
                    # if self.payroll_schedule == '2_w': # Weekly
                    #     if self.contract_id.hdmf_amount == 0:
                    #         self.hdmf_ee = hdmf_ee / 4
                    #     else:
                    #         self.hdmf_ee = self.contract_id.hdmf_amount / 4
                    #     self.hdmf_er = hdmf_er / 4

                    if self.payroll_schedule == '3_sm': # Semi-Monthly
                        if self.contract_id.hdmf_amount == 0:
                            if hdmf_period_type == '1st_2nd':
                                self.hdmf_ee = hdmf_ee / 2
                            else:
                                self.hdmf_ee = hdmf_ee
                        else:
                            if hdmf_period_type == '1st_2nd':
                                self.hdmf_ee = self.contract_id.hdmf_amount / 2
                            else:
                                self.hdmf_ee = self.contract_id.hdmf_amount

                        if hdmf_period_type == '1st_2nd':
                            self.hdmf_er = hdmf_er / 2
                        else:
                            self.hdmf_er = hdmf_er

                    # elif self.payroll_schedule == '4_m': # Monthly
                    #     if self.contract_id.hdmf_amount == 0:
                    #         self.hdmf_ee = hdmf_ee
                    #     else:
                    #         self.hdmf_ee = self.contract_id.hdmf_amount
                    #     self.hdmf_er = hdmf_er


            if self.contract_id.phic:
                if phic_period_type == payroll_period_type or phic_period_type == '1st_2nd':
                    if self.contract_id.phic_amount == 0:
                        self.phic_ee = phic_ee
                        self.phic_er = phic_er
                    else:
                        self.phic_ee = self.contract_id.phic_amount
                        self.phic_er = self.contract_id.phic_amount

            if self.contract_id.sss:
                if sss_period_type == payroll_period_type or sss_period_type == '1st_2nd':
                    if self.contract_id.sss_amount == 0:
                        self.sss_ee = sss_ee
                        self.sss_ee_mpf = sss_ee_mpf

                        if sss_conso and sss_conso_period:
                            self.sss_ee -= prev_slip.sss_ee
                            self.sss_ee_mpf -= prev_slip.sss_ee_mpf
                    else:
                        self.sss_ee = self.contract_id.sss_amount

                    self.sss_er = sss_er
                    self.sss_er_mpf = sss_er_mpf

                    if sss_conso and sss_conso_period:
                        self.sss_er -= prev_slip.sss_er
                        self.sss_er_mpf -= prev_slip.sss_er_mpf

        self.total_premium = (self.hdmf_ee + self.phic_ee + self.sss_ee + self.sss_ee_mpf)

    @api.multi
    def _get_attendance(self):
        data = {
            'work_days': 0,
            'regular_holiday': 0,
            'late': 0,
            'undertime': 0,
            'night_diff': 0,
            'night_diff_amount': 0
        }

        obj_att = self.env['hr.attendance']
        args = [
            ('employee_id', '=', self.employee_id.id),
            ('payroll_period_id', '=', self.payroll_period_id.id),
            ('state', '=', 'validate')
        ]
        attendances = obj_att.search(args)
        for att in attendances:
            if self.contract_id.has_attendance:
                if not att.dayoff and not att.is_holiday:
                    if not att.regular_schedule:
                        if not self._has_halfday_leave(att.localize_date):
                            data['work_days'] += 1
                        else:
                            data['work_days'] += 0.5    
                    else:
                        data['work_days'] += 0.5

            if self.contract_id.has_attendance and self.contract_id.compute_late:
                data['late'] += self._compute_late_deduction(att.late)

            if self.contract_id.has_attendance and self.contract_id.compute_undertime:
                # Custom rules for undertime
                if not self._has_halfday_leave(att.localize_date):
                    if att.undertime > 0:
                        if not att.is_holiday:
                            h, m = str(att.undertime).split('.')
                            if att.undertime < 1:
                                if att.undertime <= 0.5:
                                    data['undertime'] += 0.5
                                elif att.undertime > 0.5:
                                    data['undertime'] += int(h) + 1
                            else:
                                ut_diff = att.undertime - int(h)
                                if ut_diff == 0:
                                    data['undertime'] = att.undertime
                                elif ut_diff > 0 and ut_diff <= 0.5:
                                    data['undertime'] += int(h) + 0.5
                                else:
                                    data['undertime'] += int(h) + 1

            if att.night_diff_rate_id:
                hourly_rate = self.daily_pay / 8.0
                data['night_diff'] += att.night_diff
                data['night_diff_amount'] += (hourly_rate * (att.night_diff_rate_id.rate - 1)) * att.night_diff

        if self.contract_id.paid_reg_holiday and self.wage_type == 'daily':
            reg_holidays = self._get_regular_holiday()
            if reg_holidays:
                atts = []
                for att in attendances:
                    if att.localize_date not in atts:
                        atts.append(att.localize_date)

                res = [rh for rh in reg_holidays if rh in atts]
                # data['work_days'] += (len(reg_holidays) - len(res))
                # data['regular_holiday'] += (len(reg_holidays) - len(res))
                data['regular_holiday'] += len(reg_holidays)

        if self.contract_id.has_attendance:
            if data['work_days'] == 0 and data['night_diff'] == 0:
                raise ValidationError(_("No attendance found for employee - '%s' for '%s' payroll period" % (
                    self.employee_id.name, self.payroll_period_id.name)))
        return data

    def _compute_late_deduction(self, actual_late):
        obj_late_tbl = self.env['hr.late.deduction.table']

        late = actual_late * 60.0
        args = [
            ('min_fr', '<=', late),
            ('min_to', '>=', late),
        ]
        res = obj_late_tbl.search(args, limit=1)
        if res:
            late_deduct = res.late / 60.0
            return late_deduct if res else 0
        else:
            return actual_late

    # Compute Position Allowance
    def _compute_contract(self):
        res = super(Payslip, self)._compute_contract()
        adj_pa_id = self.env.ref('cml_payroll_extended.adj_position_allow').id
        self.slip_structure_ids.filtered(lambda a: a.adjustment_id.id == adj_pa_id).unlink()
        for s in self.contract_id.structure_ids.filtered(lambda a: a.state == 'open' and a.adjustment_id.id == adj_pa_id):
            if s.period_type == self.payroll_period_id.period_type or s.period_type == '1st_2nd':
                vals = {
                    'structure_line_id': s.id,
                    'adjustment_id': s.adjustment_id.id,
                    'amount': self._get_attendance()['work_days'] * s.amount
                }
                self.slip_structure_ids = [(0, 0, vals)]
        return res

    @api.multi
    def _compute_slip(self):
        for obj in self:
            oth_earn = oth_deduct = oth_tax = 0
            for ss in obj.slip_structure_ids:
                if ss.active:
                    if ss.adjustment_id.adjustment_type in ('allowance', 'otherbenefit', 'otherearning', 'refund', '13th_mo', '14th_mo'):
                        oth_earn += ss.amount
                    if ss.adjustment_id.adjustment_type in ('cashadvance', 'loan', 'otherdeduct'):
                        oth_deduct += ss.amount

                oth_tax += ss.taxable_amount

            obj.other_taxable = oth_tax
            obj.other_earning = oth_earn - oth_tax
            obj.other_deduction = oth_deduct

            # Add paid leave under Other Earnings to comply to their company policy
            obj.other_earning += (self.paid_leave * self.daily_pay)

            premiums = 0
            if not obj.contract_id.premiums_excluded:
                premiums = obj.total_premium

            obj.basic_pay = obj._get_basic_pay()
            earn = obj.basic_pay + obj.cola_amount + obj.overtime_amount + obj.night_diff_amount + obj.regular_holiday_amount
            deduct = obj.late_amount + obj.undertime_amount + premiums #+ obj.halfday_amount
            obj.gross_pay = (earn - deduct) + obj.other_taxable
            obj.wtax = obj._compute_wtax()
            obj.net_pay = (obj.gross_pay + obj.other_earning) - (obj.wtax + obj.other_deduction)

            if obj.contract_id.premiums_excluded:
                obj.net_pay -= obj.total_premium

            obj.month_13th = self._get_13th_mo_comp(obj.basic_pay, {
                    'late': obj.late_amount,
                    'ut': obj.undertime_amount,
                    'ul': 0, #obj.halfday_amount, # instead of Unpaid Leave/Absent Amount
                    'ot': obj.overtime_amount,
                    'nd': obj.night_diff_amount
                })