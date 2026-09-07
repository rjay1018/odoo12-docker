from odoo import models, fields, api, _


class FiscalYear(models.Model):
    _inherit = 'account.fiscal.year'
    _order = 'date_from desc'

    def _previous_year(self, fiscal_year_id):
        fy = self.browse(fiscal_year_id)
        args = [('date_from', '<', fy.date_from)]
        return self.search(args, order='date_from DESC', limit=1)
