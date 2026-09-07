from odoo import models, fields, api, _

class MrpProductionExtension(models.Model):
    _inherit = 'mrp.production'

    sales_price = fields.Float(string="Sales Price", compute="_compute_sales_price", store=True)
    profit = fields.Float(string="Profit %", compute="compute_profit", store=True)

    total_material_cost = fields.Float(store=True)
    total_labour_cost = fields.Float(store=True)
    total_overhead_cost = fields.Float(store=True)
    total_all_cost = fields.Float(store=True)
    total_actual_labour_cost = fields.Float(store=True)
    total_actual_overhead_cost = fields.Float(store=True)


    @api.depends('product_id')
    def _compute_sales_price(self):
        for rec in self:
            rec.sales_price = rec.product_id.lst_price

    @api.depends('sales_price', 'total_all_cost')
    def compute_profit(self):
        for rec in self:
            if rec.sales_price != 0:
                rec.profit = rec.sales_price - rec.total_all_cost / rec.sales_price




