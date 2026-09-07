# -*- coding: utf-8 -*-

from odoo import api, fields, models


class manpower_request(models.Model):

    _name = "manpower.recruit.request"
    _inherit = ['mail.thread','mail.activity.mixin']

    STATES = [
        ('draft', 'Draft'),
        ('request', 'Requested'),
        ('validate','Validated'),
        ('approve', 'Approved'),
        ('cancel', 'Canceled'),
    ]
    sequence = fields.Char(
        "Sequence",
        readonly=True
    )
    user_id=fields.Many2one(
        'res.users',
        required=True,
        string='User',
        readonly=1,
        default=lambda self: self.env.user.id
    )
    name = fields.Char(
        required=True,
        string="Name"
    )
    manpower = fields.Integer(
        string="Manpower"
    )
    description = fields.Text(
        string="Description"
    )
    job_location_id = fields.Many2one(
        'res.partner',
        string="Job Location",
        store = True,
        domain=[('is_company','=',True)]
    )
    department_id = fields.Many2one(
        'hr.department',
        string="Department"
    )
    job_position = fields.Many2one(
        'hr.job',
        string="Job Position"
    )
    operation_type = fields.Selection(
        [
            ('create','Create New Record'),
            ('update','Update Existing Record')
        ],
        string="Operation Type"
    )
    state = fields.Selection(
        STATES,
        default='draft',
        track_visibility='onchange'
    )

    @api.multi
    def send_request_state(self):
        self.state = 'request'

    @api.multi
    def validate_state(self):
        self.state = 'validate'
        
    @api.multi
    def approve_state(self):
        if self.operation_type == 'create':
            self.env['hr.job'].sudo().create({
                'name' : self.name,
                'department_id' : self.department_id.id,
                'user_id' : self.user_id.id,
                'address_id' : self.job_location_id.id,
                'no_of_recruitment' : self.manpower,
                'description' : self.description,
                'manpower_request_id' : self.id
            })
        elif self.operation_type == 'update':
            job_id = self.job_position#self.env['hr.job'].sudo().browse(self.job_position.id)
            job_id.write({
                'name' : self.name,
                'department_id' : self.department_id.id,
                'user_id' : self.user_id.id,
                'address_id' : self.job_location_id.id,
                'no_of_recruitment' : self.manpower,
                'description' : self.description,
                'manpower_request_id' : self.id
            })
        self.state = 'approve'
    
    @api.onchange('operation_type','job_position')
    def onchange_job(self):
        for record in self:
            if record.operation_type == 'update' and record.job_position:
                record.department_id = record.job_position.department_id
                record.job_location_id = record.job_position.address_id
                record.manpower = record.job_position.no_of_recruitment
                record.description = record.job_position.description
                record.name = record.job_position.name
            elif record.operation_type == 'create':
                record.department_id = ""
                record.job_location_id = ""
                record.manpower = ""
                record.description = ""
                record.name = ""
                record.job_position = ""
    
    @api.model
    def create(self, vals):
        vals['sequence'] = self.env['ir.sequence'].next_by_code('manpower.recruit.request')
        return super(manpower_request, self).create(vals)

    @api.multi
    def cancel_state(self):
        self.state = 'cancel'
    