from odoo import api, fields, models, _

class PartnerStage(models.Model):
    _name = "client.support"
    
    name = fields.Char(
        string = 'Name',
        help = 'Preferred Support Type', 
        required =True
    )
    description = fields.Html(
        string='Description',
    )

    product_id = fields.Many2one(
        string='Related Product',
        comodel_name='product.product',
        domain=[('type','=','service',)]
    )
    
