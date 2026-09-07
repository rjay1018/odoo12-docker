from odoo import models,api,fields

class hr_employee(models.Model):
    _inherit = 'hr.employee'
    
    country_id = fields.Many2one(
        groups="hr.group_hr_user,base.group_user"
    )
    identification_id = fields.Char(
        groups="hr.group_hr_user,base.group_user"
    )
    passport_id = fields.Char(
        groups="hr.group_hr_user,base.group_user"
    )
    bank_account_id = fields.Many2one(
        groups="hr.group_hr_user,base.group_user"
    )
    address_home_id = fields.Many2one(
        groups="hr.group_hr_user,base.group_user"
    )
    emergency_contact = fields.Char(
        groups="hr.group_hr_user,base.group_user"
    )
    emergency_phone = fields.Char(
        groups="hr.group_hr_user,base.group_user"
    )
    km_home_work = fields.Integer(
        groups="hr.group_hr_user,base.group_user"
    )
    gender = fields.Selection(
        groups="hr.group_hr_user,base.group_user"
    )
    marital = fields.Selection(
        groups="hr.group_hr_user,base.group_user"
    )
    spouse_complete_name = fields.Char(
        groups="hr.group_hr_user,base.group_user"
    )
    spouse_birthdate = fields.Date(
        groups="hr.group_hr_user,base.group_user"
    )
    children = fields.Integer(
        groups="hr.group_hr_user,base.group_user"
    )
    birthday = fields.Date(
        groups="hr.group_hr_user,base.group_user"
    )
    place_of_birth = fields.Char(
        groups="hr.group_hr_user,base.group_user"
    )
    country_of_birth = fields.Many2one(
        groups="hr.group_hr_user,base.group_user"
    )
    visa_no = fields.Char(
        groups="hr.group_hr_user,base.group_user"
    )
    permit_no = fields.Char(
        groups="hr.group_hr_user,base.group_user"
    )
    visa_expire = fields.Date(
        groups="hr.group_hr_user,base.group_user"
    )
    certificate = fields.Selection(
        groups="hr.group_hr_user,base.group_user"
    )
    study_field = fields.Char(
        groups="hr.group_hr_user,base.group_user"
    )
    study_school = fields.Char(
        groups="hr.group_hr_user,base.group_user"
    )
    google_drive_link = fields.Char(
        groups="hr.group_hr_user,base.group_user"
    )
    additional_note = fields.Text(
        groups="hr.group_hr_user,base.group_user"
    )
