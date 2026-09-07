from odoo import api, fields, models, _

class PartnerStage(models.Model):
    _name = "client.stage"
    _order = "sequence"

    name = fields.Char(string = 'Partner Stages', help = 'Enter Stages for Partners', required =True)
    sequence = fields.Integer(string = 'Sequence', help = 'Enter Sequence Number')


