# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrEmergencyContactInherit(models.Model):
    _inherit = 'hr.emergency.contact'

    number = fields.Char(string='Contact Number', help='Contact Number')
    relation = fields.Char(string='Name of Contact Person', help='Relation with employee')
    relationship = fields.Char(string='Relationship', help='Relation with employee')


class HrEmployeeFamilyInfo(models.Model):

    _inherit = 'hr.employee.family'
    
    relation = fields.Selection([('father', 'Father'),
                                 ('mother', 'Mother'),
                                 ('daughter', 'Daughter'),
                                 ('son', 'Son'),
                                 ('wife', 'Spouse'),
                                 ('sibling', 'Sibling'),
                                 ('partner', 'Live-in Partner'),
                                 ('others','Others')], string='Relationship', help='Relation with employee')
    fam_birthday = fields.Date(string='Birthday')
    emergency_number = fields.Char(
        string='Emergency Contact', help='Contact number in case of emergency'
    )
    hmo_applied = fields.Boolean(
        string='HMO Applied',
    )
    

class Employee(models.Model):
    _inherit = "hr.employee"

    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('cohabitant', 'Common Law Spouse'),
        ('widower', 'Widower'),
        ('separated', 'Separated'),
        ('divorced', 'Divorced')
    ], string='Marital Status', groups="hr.group_hr_user", default='single')

    provincial_address = fields.Text(String='Permanent Address')
    
    source_id = fields.Many2one(
        'utm.source',
        string="Source",
        copy=False
    )
    employee_status = fields.Selection([
        ('trainee', 'Trainee'),
        ('propitionary', 'Probationary'),
        ('regular', 'Regular'),
        ('regular_no', 'Regular No Earnings'),
        ('project', 'Project Base'),
        ('separated_rs', 'Separated Resigned'),
        ('separated_rt', 'Separated Retired'),
        ('separated_f', 'Separated Failed'),
        ('separated_l', 'Separated Leave'),
        ('separated_d', 'Separated Deceased'),
        ('separated_t', 'Separated Terminated')],
        string="Employment Status"
    )
    date_regularized = fields.Date(string='Date Regularized')
    date_separated = fields.Date(string='Date Separated')
    
    #Philippine Mandated ID Information
    sssid = fields.Char(
        string='SSS',
        groups="hr.group_hr_user",
        help='Social Security System Number'
    )
    tinid = fields.Char(
        string='TIN',
        groups="hr.group_hr_user",
        help='Tax Identification Number'
    )
    philhealthid = fields.Char(
        string='PhilHealth',
        groups="hr.group_hr_user",
        help='PhilHealth Number'
    )
    pagibigid = fields.Char(
        string='Pag-ibig', 
        groups="hr.group_hr_user",
        help='Pag-ibig Number'
    )
    hmoid = fields.Char(
        string='HMO Policy Number', 
        groups="hr.group_hr_user",
        help='HMO Policy Number'
    )
