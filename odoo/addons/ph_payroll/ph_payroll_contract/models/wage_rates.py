from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Regions(models.Model):
    _name = 'res.country.region'

    @api.multi
    @api.depends('code', 'name')
    def name_get(self):
        res = []
        for r in self:
            name = "(%s) %s" % (r.code, r.name)
            res += [(r.id, name)]
        return res

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    description = fields.Text()


class WageRates(models.Model):
    _name = 'hr.wage.rate'

    SECTOR = [
        ('all', 'All Sectors/Industries'),
        ('non_agri', 'Non-Agriculture'),
        ('agri', 'Agriculture'),
    ]

    AGRICULTURE = [
        ('plant', 'Plantation'),
        ('non_plant', 'Non-Plantation')
    ]

    ESTABLISHMENT = [
        ('retail_service_15less', 'Retail/Service Establishments employing 15 workers or less'),
        ('retail_service_10more', 'Retail/Service Establishments employing more than 10'),
        ('retail_service_10less', 'Retail/Service Establishments employing not more than 10'),
        ('manufacturing', 'Manufacturing Establishments regularly employing less than 10 workers'),
    ]

    EMPLOYMENT_SIZE = [
        ('30_more', '30 or more employees'),
        ('10_29', '10 to 29 employees'),
        ('1_9_3m_15m', '1 to 9 employees: Category above 3M-15M'),
        ('1_9_3m_below', '1 to 9 employees: Category 3M and below'),
    ]

    @api.multi
    @api.depends('region_id', 'sector', 'basic_wage', 'cola')
    def name_get(self):
        res = []
        for r in self:
            sector = [v for k, v in self.SECTOR if k == r.sector][0]
            name = "%s, %s, Basic: %s, COLA: %s" % (
                    r.region_id.code,
                    sector,
                    '{:.2f}'.format(r.basic_wage),
                    '{:.2f}'.format(r.cola)
                )
            res += [(r.id, name)]
        return res

    region_id = fields.Many2one('res.country.region', 'Region', required=True)
    sector = fields.Selection(SECTOR, string='Sector/Industry', required=True)
    agriculture = fields.Selection(AGRICULTURE)
    establishment = fields.Selection(ESTABLISHMENT)
    area = fields.Char()
    employment_size = fields.Selection(EMPLOYMENT_SIZE)
    basic_wage = fields.Float(required=True)
    cola = fields.Float('COLA', required=True)
    min_wage_rate = fields.Float(compute='_compute_min_wage_rate', string='Min. Wage Rate', store=True)

    @api.depends('basic_wage', 'cola')
    def _compute_min_wage_rate(self):
        self.min_wage_rate = self.basic_wage + self.cola
