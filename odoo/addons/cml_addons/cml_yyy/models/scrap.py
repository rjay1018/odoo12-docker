from odoo import fields, models, api


class StockScrapYYY(models.Model):  
    _inherit = 'stock.scrap'

    notes = fields.Html("More Infomation")