# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    def _compute_stage_duration(self):
        delta = None
        now = datetime.now()
        last_stage = self.application_stage_ids.sorted(key=lambda s: s.create_date)
        if last_stage:
            delta = now - last_stage[-1].create_date
        else:
            delta = now - self.create_date
        return delta.days if delta else 0

    @api.multi
    def write(self, vals):
        res = super(HrApplicant, self).write(vals)
        if 'stage_id' in vals:
            duration = self._compute_stage_duration()
            for obj in self:
                obj.application_stage_ids = [(0, 0, {
                        'applicant_id': self.id,
                        'stage_id': vals['stage_id'],
                        'duration': duration
                    })]
        return res
    
    refusal_reason_id = fields.Many2one(
        string='Reason',
        comodel_name='refusal.reasons',
    )
    address_id = fields.Many2one(
        string='Job Location',
        related='job_id.address_id',
        readonly=True,
        store=True
    )
    date_applied = fields.Date('Date Applied')
    application_stage_ids = fields.One2many('hr.application.stage', 'applicant_id',string='Stages')

    @api.multi
    def archive_applicant(self):
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'refusal.wizard',
            'target': 'new',
        }


class ApplicationStage(models.Model):
    _name = 'hr.application.stage'
    _order = 'create_date'

    applicant_id = fields.Many2one('hr.applicant')
    stage_id = fields.Many2one('hr.recruitment.stage', 'Stage')
    create_date = fields.Datetime('Date')
    date_last_stage_update = fields.Datetime()
    duration = fields.Integer('Duration (Days)')


class RefusalReasons(models.Model):
    _name = 'refusal.reasons'
    _description = 'Applicant Refusal Reasons'

    name = fields.Char(
    	string='Reasons',
    	size=64,
    	required=True,
    )