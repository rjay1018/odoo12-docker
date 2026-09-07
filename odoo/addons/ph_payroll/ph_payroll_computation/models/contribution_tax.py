from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HDMF(models.Model):
    _name = 'hdmf.table'
    _order = 'mo_salary_fr'

    COMP = [
        ('pct', 'Percentage'),
        ('fix', 'Fix Rate')
    ]

    @api.multi
    @api.depends('mo_salary_fr', 'mo_salary_to')
    def name_get(self):
        res = []
        for r in self:
            name = '%s - %s' % (self.mo_salary_fr, self.mo_salary_to)
            res += [(r.id, name)]
        return res

    @api.one
    @api.depends('ee_rate', 'er_rate')
    def _compute_total(self):
        if self.er_computation == 'pct':
            self.total = self.ee_rate + self.er_rate
        else:
            self.total = self.ee_rate

    @api.onchange('er_computation')
    def onchange_er_comp(self):
        if self.er_computation == 'fix':
            self.er_rate = 100
        else:
            self.er_rate = 2

    mo_salary_fr = fields.Float(string='From')
    mo_salary_to = fields.Float(string='To')
    ee_rate = fields.Float(string='EE Contribution Rate (%)')
    er_computation = fields.Selection(COMP, string='Computation - ER', default='fix')
    er_rate = fields.Float(string='ER Contribution Rate (% or Fix)')
    total = fields.Float(compute='_compute_total', string='Total (%)')

    def _get_hdmf(self, salary):
        data = {
            'ee': 0,
            'er': 0
        }
        args = [('mo_salary_fr', '<=', salary), ('mo_salary_to', '>=', salary)]
        hdmf = self.search(args, limit=1)
        if hdmf:
            data['ee'] = salary * (hdmf[0].ee_rate / 100.0)
            if hdmf.er_computation == 'pct':
                data['er'] = salary * (hdmf[0].er_rate / 100.0)
            else:
                data['er'] = hdmf.er_rate
        return data


class PHIC(models.Model):
    _name = 'phic.table'
    _order = 'mo_salary_fr'

    @api.multi
    @api.depends('mo_salary_fr', 'mo_salary_to')
    def name_get(self):
        res = []
        for r in self:
            name = '%s - %s' % (str(self.mo_salary_fr), str(self.mo_salary_to))
            res += [(r.id, name)]
        return res

    @api.one
    @api.depends('mo_salary_fr', 'mo_salary_to', 'premium_rate')
    def _compute_premium(self):
        mo_premium = ''
        pr = self.premium_rate / 100.0

        if self.mo_salary_fr == 0:
            amt = self.mo_salary_to * pr
            mo_premium = str(round(amt,2))
        else:
            amt_fr = self.mo_salary_fr * pr
            amt_to = self.mo_salary_to * pr
            mo_premium = '%s - %s' % (str(round(amt_fr,2)), str(round(amt_to,2)))

        self.mo_premium = mo_premium

    mo_salary_fr = fields.Float(string='From')
    mo_salary_to = fields.Float(string='To')
    premium_rate = fields.Float(string='Premium Rate (%)')
    mo_premium = fields.Char(string='Monthly Premium', compute='_compute_premium')

    def _get_phic(self, salary):
        data = {
            'ee': 0,
            'er': 0
        }
        args = [('mo_salary_fr', '<=', salary), ('mo_salary_to', '>=', salary)]
        phic = self.search(args, limit=1)
        if phic:
            amount = salary * (phic[0].premium_rate / 100.0)
            data['ee'] = amount / 2
            data['er'] = amount / 2
        return data


class SSS(models.Model):
    _name = 'sss.table'
    _order = 'mo_salary_fr'

    @api.multi
    @api.depends('mo_salary_fr', 'mo_salary_to')
    def name_get(self):
        res = []
        for r in self:
            name = '%s - %s' % (self.mo_salary_fr, self.mo_salary_to)
            res += [(r.id, name)]
        return res

    @api.one
    @api.depends('er_rate', 'ee_rate', 'ec_er_rate', 'mpf_er_rate', 'mpf_ee_rate')
    def _compute_total(self):
        mpf = self.mpf_er_rate + self.mpf_ee_rate
        self.er_ee_ss_total = self.er_rate + self.ee_rate
        self.mpf_total = mpf
        self.er_total = self.er_rate + self.ec_er_rate + self.mpf_er_rate
        self.ee_total = self.ee_rate + self.mpf_ee_rate
        self.total = self.er_rate + self.ee_rate + self.ec_er_rate + mpf

    active = fields.Boolean(default=True)
    mo_salary_fr = fields.Float(string='From')
    mo_salary_to = fields.Float(string='To')
    er_rate = fields.Float(string='Regular SS - ER')
    ee_rate = fields.Float(string='Regular SS - EE')
    er_ee_ss_total = fields.Float(compute='_compute_total', string='Reg. SS Total', store=True)
    ec_er_rate = fields.Float(string='EC - ER')
    mpf_er_rate = fields.Float(string='MPF - ER')
    mpf_ee_rate = fields.Float(string='MPF - EE')
    mpf_total = fields.Float(compute='_compute_total', string='MPF Total', store=True)
    er_total = fields.Float(compute='_compute_total', string='Total ER', store=True)
    ee_total = fields.Float(compute='_compute_total', string='Total EE', store=True)
    total = fields.Float(compute='_compute_total', store=True)

    def _get_sss(self, salary):
        data = {
            'er': 0,
            'ee': 0,
            'mpf_er': 0,
            'mpf_ee': 0
        }
        args = [('mo_salary_fr', '<=', salary), ('mo_salary_to', '>=', salary)]
        sss = self.search(args, limit=1)
        if sss:
            data['er'] = sss[0].er_rate + sss[0].ec_er_rate
            data['ee'] = sss[0].ee_rate
            data['mpf_er'] = sss[0].mpf_er_rate
            data['mpf_ee'] = sss[0].mpf_ee_rate
        return data


class WTax(models.Model):
    _name = 'wtax.table'
    _order = 'payroll_period, range_to'

    PAYROLL_PERIOD = [
        ('1_d', 'Daily'),
        ('2_w', 'Weekly'),
        ('3_sm', 'Semi-Monthly'),
        ('4_m', 'Monthly')
    ]

    payroll_period = fields.Selection(PAYROLL_PERIOD)
    range_fr = fields.Float(string='From')
    range_to = fields.Float(string='To')
    prescribed_wtax = fields.Float(string='Prescribed Withholding Tax')
    tax_on_excess = fields.Float(string='Tax on Excess (%)')

    def _get_wtax(self, gross_pay, payroll_schedule):
        amount = 0
        args = [('range_fr', '<=', gross_pay), ('range_to', '>=', gross_pay), ('payroll_period', '=', payroll_schedule)]
        wtax = self.search(args, limit=1)
        if wtax:
            if wtax.tax_on_excess > 0:
                amount = ((gross_pay - wtax.range_fr) * (wtax.tax_on_excess / 100.0)) + wtax.prescribed_wtax
        return amount


class PremiumsTaxConfig(models.Model):
    _name = 'hr.premiums.tax.config'
    _order = 'name'

    PERIOD_TYPE = [
        ('1st_2nd', '1st Half & 2nd Half'),
        ('1st', '1st Half'),
        ('2nd', '2nd Half')
    ]

    name = fields.Char(required=True)
    period_type = fields.Selection(PERIOD_TYPE, required=True, default='1st_2nd',
        help='The period to which premiums and tax will be process')

    ga_ee_credit_account_id = fields.Many2one('account.account', string='EE - Credit Account')
    ga_er_debit_account_id = fields.Many2one('account.account', string='ER - Debit Account')
    er_credit_account_id = fields.Many2one('account.account', string='ER - Credit Account')
    journal_id = fields.Many2one('account.journal', string='Journal')

    sss_ee_mpf_credit_account_id = fields.Many2one('account.account', string='EE - Credit Account')
    sss_er_mpf_debit_account_id = fields.Many2one('account.account', string='ER - Debit Account')
    sss_er_mpf_credit_account_id = fields.Many2one('account.account', string='ER - Credit Account')

    def _get_premium_tax_data(self, premiums_tax):
        hdmf = self.env.ref('ph_payroll_computation.prem_tax_config_hdmf', None)
        phic = self.env.ref('ph_payroll_computation.prem_tax_config_phic', None)
        sss = self.env.ref('ph_payroll_computation.prem_tax_config_sss', None)
        wtax = self.env.ref('ph_payroll_computation.prem_tax_config_wtax', None)

        if premiums_tax == 'hdmf': rec_id = hdmf.id if hdmf else None
        elif premiums_tax == 'phic': rec_id = phic.id if phic else None
        elif premiums_tax == 'sss': rec_id = sss.id if sss else None
        else: rec_id = wtax.id if wtax else None
        return self.browse(rec_id)
