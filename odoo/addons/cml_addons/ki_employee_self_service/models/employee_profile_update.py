# -*- coding: utf-8 -*-

from odoo import api, fields, models


class HrEmployeeContractName(models.Model):

    _inherit = 'hr.emergency.contact'


    profile_update_id = fields.Many2one(
        'employee.profile.update',
        string="Profile Update"
    )

class employee_profile_update(models.Model):

    _name = "employee.profile.update"
    _inherit = ['mail.thread','mail.activity.mixin']

    STATES = [
        ('draft', 'Draft'),
        ('request', 'Request'),
        ('approve', 'Approve'),
        ('cancel', 'Cancel'),
    ]
    name = fields.Char(
        string="Sequence"
    )
    
    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        required=True
    )
    date_request = fields.Date(
        default=fields.Date.context_today
    )
    work_email = fields.Char(
        string="Work Email"
    )
    work_mobile = fields.Char(
        string="Work Mobile"
    )
    additional_notes = fields.Text(
        string="Additional Notes"
    )
    state = fields.Selection(
        STATES,
        default='draft',
        track_visibility='onchange'
    )
    emergency_contacts = fields.One2many(
        'hr.emergency.contact',
        'profile_update_id',
        string='Emergency Contact'
    )
    civil_status = fields.Selection([
            ('single', 'Single'),
            ('married', 'Married'),
            ('cohabitant', 'Legal Cohabitant'),
            ('widower', 'Widower'),
            ('divorced', 'Divorced')
        ], 
        string='Civil Status', 
        default='single'
    )
    
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('employee.profile.update')
        return super(employee_profile_update, self).create(vals)
    
    @api.model
    def default_get(self, fields_list):
        result = super(employee_profile_update, self).default_get(fields_list)
        user = self.env.user
        employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if employee:
            result.update({
                'employee_id': employee.id
            })
        return result

    @api.onchange('employee_id')
    def _set_employee_data(self):
        self.work_email = self.employee_id.work_email
        self.work_mobile = self.employee_id.mobile_phone
        self.additional_notes = self.employee_id.additional_note
        self.civil_status  = self.employee_id.marital
        if self.employee_id.emergency_contacts:
            self.emergency_contacts = [(6, 0, self.employee_id.emergency_contacts.ids)]#[(6, i.id) for i in self.employee_id.emergency_contacts]
            
    @api.multi
    def send_request_state(self):
        self.state = 'request'

    @api.multi
    def cancel_state(self):
        self.state = 'cancel'

    @api.multi
    def approve_state(self):
        for record in self:
            
            record.employee_id.work_email = record.work_email
            record.employee_id.mobile_phone = record.work_mobile
            record.employee_id.additional_note = record.additional_notes
            record.employee_id.marital = record.civil_status
            record.employee_id.emergency_contacts = [(6, 0, record.emergency_contacts.ids)]
            record.state = 'approve'
