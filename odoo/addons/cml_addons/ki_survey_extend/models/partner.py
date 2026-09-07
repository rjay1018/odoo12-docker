from odoo import models,fields,api

class res_relative(models.Model):
    _name='res.partner.relative'

    partner_id = fields.Many2one(
        'res.partner'
    )
    relation_type = fields.Selection(
        [
            ('self', 'Self'),
            ('father', 'Parent'),
            ('teacher', 'Teacher'),
            ('guardian', 'Guardian')
        ]
    )
    email = fields.Char(
        "Email",
        required=True
    )

class Res_part(models.Model):
    _inherit = 'res.partner'

    relatives_ids = fields.One2many(
        'res.partner.relative',
        'partner_id'
    )