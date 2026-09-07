from odoo import models,fields,api

class Survey_categ(models.Model):
    _name = 'survey.user.category'
    _description = 'Survey Category'

    name = fields.Char(
        "Name",
        required=True
    )