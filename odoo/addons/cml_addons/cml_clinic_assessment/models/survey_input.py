# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SurveyUser_input(models.Model):
    _inherit = 'survey.user_input'

    specialist_score = fields.Float(
        string='Specialist Score',
        states={'submitted': [('readonly', True)]},   
    )
    specialist_notes = fields.Text(
        string='Specialist Notes',
        states={'submitted': [('readonly', True)]},
    )
    
    state = fields.Selection(selection_add=[('submitted', "Submitted")])
    

    def action_submit(self):
        self.write({'state': 'submitted'})