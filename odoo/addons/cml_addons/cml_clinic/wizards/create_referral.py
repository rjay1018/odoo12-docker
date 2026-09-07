# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CreateReferral(models.TransientModel):
    _name = 'create.referral'
    _description = 'Create Referral Request'

    
    partner_id = fields.Many2one(
        string='Client',
        comodel_name='res.partner',
        required=True,
        readonly=True,
        domain=[('customer','=','True',)]
    )
    support_id = fields.Many2one(
        string='Support',
        comodel_name='client.support',
        required=True,
        ondelete='restrict',
    )
    reason = fields.Text(
        string='Reason for Referral',
        required=True
        
    )
    user_id = fields.Many2one(
        string="Requested By",
        comodel_name='res.users',
        default=lambda self: self.env.uid
    )
    source = fields.Char(
        string='Source',
    )

    def action_create(self):
        vals = {
             'partner_id'   : self.partner_id.id,
             'support_id'  : self.support_id.id,
             'source' : self.source,
             'reason' : self.reason,
             'user_id' : self.user_id.id
        }
        self.env['client.referral'].create(vals)