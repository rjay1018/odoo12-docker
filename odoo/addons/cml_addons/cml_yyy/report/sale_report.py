from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    partner_shipping_id = fields.Many2one('res.partner', 'Delivery Address', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['partner_shipping_id'] = ", s.partner_shipping_id as partner_shipping_id"
        groupby += ', s.partner_shipping_id'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)