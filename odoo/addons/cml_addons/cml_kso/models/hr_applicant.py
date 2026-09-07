# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrApplicant(models.Model):
    _inherit = 'hr.applicant'
    
    refusal_reason_id = fields.Many2one(
        string='Reason',
        comodel_name='refusal.reasons',

    )

    @api.multi
    def archive_applicant(self):
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'refusal.wizard',
            'target': 'new',
        }

class RefusalReasons(models.Model):
    _name = 'refusal.reasons'
    _description = 'Applicant Refusal Reasons'

    name = fields.Char(
    	string='Reasons',
    	size=64,
    	required=True,
    )