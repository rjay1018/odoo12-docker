# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime, timedelta


class ClientReferral(models.Model):
    _name = 'client.referral'
    _description = 'Client Referral Request'

    _rec_name = 'name'
    _order = 'name ASC'

    @api.model
    def create(self, vals):
        if vals.get('name', ('New')) == ('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('clinic.referral.sequence') or ('New')
        result = super(ClientReferral, self).create(vals)
        return result
    
    name = fields.Char(
        string='Name',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: ('New')
    )
    partner_id = fields.Many2one(
        string='Client',
        comodel_name='res.partner',
        required=True,
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
    )
    user_id = fields.Many2one(
        string="Requested By",
        comodel_name='res.users',
        default=lambda self: self.env.uid
    )
    source = fields.Char(
        string='Source',
    )
    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'), ('confirmed', 'Confirmed'),  ('done', 'Done'),  ('cancel', 'Cancel')],
        default='draft',
        readonly=True,
    )
    requested_date = fields.Date(
        string='Requested Date',
        required=False,
        readonly=False,
        index=False,
        default=lambda now: fields.Date.context_today(now),
        help=False
    )
    
    @api.multi
    def action_confirm(self):
        self.write({'state': 'confirmed'})
    
    @api.multi
    def action_draft(self):
        self.write({'state': 'draft'})
    
    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})
    
    @api.multi
    def action_done(self):
        self.write({'state': 'done'})
    
    
    