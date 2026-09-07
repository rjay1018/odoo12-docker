from odoo import models, fields, api


class SurveyQuestion(models.Model):
    _inherit = 'survey.question'

    link_partner = fields.Boolean(
        string="Link Partner"
    )
    partner_field_name = fields.Selection(
        [('name', 'Name'),
         ('email', 'Email'),
         ('mobile', 'Mobile'), ('birthday', 'Birthday')
         ],
        string="Partner Type"
    )

    def action_update_description(self):
        for rec in self:
            if rec.description == '<p><br></p>':
                rec.update({'description': False})
