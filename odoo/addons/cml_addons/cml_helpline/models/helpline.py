# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError



class HelplineSessions(models.Model):
    _name = 'helpline.sessions'
    _description = 'Helpline Sessions'

    _rec_name = 'name'
    _order = 'name ASC'

    @api.model
    def create(self, vals):
        if vals.get('name', ('New')) == ('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('helpline.sequence') or ('New')
        result = super(HelplineSessions, self).create(vals)
        return result
    
    @api.constrains('start_time','end_time')
    def _check_start_time(self):
        for t in self:
            if t.start_time < 00.00 or t.start_time > 23.59 :
                raise ValidationError(('The Time Start value must be between 0:00 and 23:59!'))
            if  t.end_time < t.start_time or t.end_time > 23.59:
                raise ValidationError(('The Time End value must be between START TIME and 23:59!'))  


    name = fields.Char(
        string='Call ID',
        required=True,
        default=lambda self: ('New'),
        copy=False
    )
    
    client_name = fields.Char(
        string='Caller Name',
        states={'draft': [('readonly', False)]}
    )

    age = fields.Integer(
        string='Age',
        states={'draft': [('readonly', False)]},
    )
    
    organization = fields.Char(
        string='Organization',
        states={'draft': [('readonly', False)]},
    )

    partner_id = fields.Many2one(
        string='Link to Client',
        comodel_name='res.partner',
        ondelete='cascade',
        states={'draft': [('readonly', False)]},
    )
        
    date_of_seassion = fields.Date(
        string='Date of Sessions',
        states={'draft': [('readonly', False)]},
        default=fields.Date.context_today,
    )
    
    start_time = fields.Float(
        string='Start Time of Call',
        states={'draft': [('readonly', False)]},
    )
    
    end_time = fields.Float(
        string='End Time of Call',
        states={'draft': [('readonly', False)]},
    )
    
    language = fields.Many2one(
        string='Language',
        comodel_name='call.language',
        states={'draft': [('readonly', False)]},
        ondelete='cascade',
    )
    
    extension = fields.Char(
        string='Extension Number',
        related='user_id.employee_ids.extension',
        readonly=True,
        store=True
    )

    employee_id = fields.Many2one(
        string='Employee',
        comodel_name='hr.employee',
        states={'draft': [('readonly', False)]},
        ondelete='cascade',
    )

    user_id = fields.Many2one(
        comodel_name='res.users',
        string="Agent", 
        default=lambda 
        self: self.env.uid
    )
    
    case_category_ids = fields.Many2many(
        string='Call Tag',
        comodel_name='case.category',
        relation='case_category_helpline_rel',
        column1='case_category_id',
        column2='helpline_id',
    )
    
    caller_type_id = fields.Many2one(
        string='Caller Type',
        comodel_name='call.type',
        states={'draft': [('readonly', False)]},
        ondelete='cascade',
    )
    
    summary = fields.Text(
        string='Summary of Concerns',
        states={'draft': [('readonly', False)]},
    )    
    
    oars = fields.Text(
        string='PLEASE DESCRIBE THE CALL IN TERMS OF Open-ended Questions, Affirmations , Reflections, S - Summarizations.  (O.A.R.S.)',
        states={'draft': [('readonly', False)]},
    )
    
    conclusion = fields.Text(
        string='Conclusion',
        states={'draft': [('readonly', False)]},
    )
    
    contact = fields.Char(
        string='Contact Number',
        states={'draft': [('readonly', False)]},
    )
    
    schedule_followup = fields.Datetime(
        string='Schedule Followup',
        states={'draft': [('readonly', False)]},
        default=fields.Datetime.now,
    )
    
    followup_call = fields.Boolean(
        string='Followup Call',
        states={'draft': [('readonly', False)]},
    )
    
    notes = fields.Text(
        string='How did you feel about the call? Do you have any questions? Please indicate below if you are in need of debriefing.',
        states={'draft': [('readonly', False)]},
    )

    for_debrief = fields.Boolean(
        string='Request Debriefing',
        states={'draft': [('readonly', False)]},
    )
    
    sup_notes = fields.Text(
        string='Supervisor Notes.',
        readonly=True,
        states={'done': [('readonly', False)]},
    )
    
    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'), ('done', 'Done'),  ('validated', 'Validated'),  ('drop', 'Drop')],
        default='draft',
        readonly=True,
    )

    is_client = fields.Boolean(
        string='Is Client',
        states={'draft': [('readonly', False)]}
    )
    
    @api.multi
    def action_done(self):
        self.write({'state': 'done'})
    
    @api.multi
    def action_draft(self):
        self.write({'state': 'draft'})
    
    @api.multi
    def action_drop(self):
        self.write({'state': 'drop'})
    
    @api.multi
    def action_validated(self):
        self.write({'state': 'validated'})