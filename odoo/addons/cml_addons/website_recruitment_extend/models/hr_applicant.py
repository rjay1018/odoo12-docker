# -*- coding: utf-8 -*-
# Part of Kiran Infosoft. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    firstname = fields.Char(
        string="First Name",
        copy=False
    )
    middlename = fields.Char(
        string="Middle Name",
        copy=False
    )
    lastname = fields.Char(
        string="Last Name",
        copy=False
    )

    birthday = fields.Date(
        string="Birth Date",
        copy=False
    )
    gender = fields.Selection(
        selection=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other')
        ],
        default="male",
        string="Gender"
    )
    marital = fields.Selection(
        selection=[
            ('single', 'Single'),
            ('married', 'Married (or similar)'),
            ('widower', 'Widower'),
            ('divorced', 'Divorced')
        ],
        string='Civil Status',
        default='single'
    )
    age = fields.Integer(
        string="Age"
    )
    children = fields.Integer(
        string="No. Of Children"
    )
    # Education Attaintment
    edu_schoolname = fields.Char(
        string="School Name",
        copy=False
    )
    edu_coursename = fields.Char(
        string="Course Name",
        copy=False
    )
    edu_graduate_year = fields.Char(
        string="Year Graduated",
        copy=False
    )
    edu_level_year = fields.Char(
        string="Year Level Attained",
        copy=False
    )

    # Work Experience
    work_position = fields.Char(
        string="Position",
        copy=False
    )
    work_employer = fields.Char(
        string="Employer",
        copy=False
    )
    work_supervisor = fields.Char(
        string="Supervisor",
        copy=False
    )
    work_contact_number = fields.Char(
        string="Contact Number",
        copy=False
    )
    work_start_date = fields.Date(
        string="Employment Date",
        copy=False
    )
    work_end_date = fields.Date(
        string="Separation Date",
        copy=False
    )

    # contact address
    contact_street = fields.Char(
        string="Street",
        copy=False
    )
    contact_street2 = fields.Char(
        string="Street2",
        copy=False
    )
    contact_zip = fields.Char(
        string="Zip",
        copy=False
    )
    contact_zone = fields.Char(
        string="Zone",
        copy=False
    )
    contact_city = fields.Char(
        string="City",
        copy=False
    )
    contact_country_id = fields.Many2one(
        'res.country',
        string="Country",
        copy=False
    )

    @api.model_cr
    def init(self):
        field_list = [
            'birthday',
            'source_id',
            'edu_schoolname',
            'edu_coursename',
            'edu_graduate_year',
            'edu_level_year',
            'description',
            'work_position',
            'work_employer',
            'work_supervisor',
            'work_contact_number',
            'work_start_date',
            'work_end_date',
            'reference',
            'contact_street',
            'contact_zone',
            'contact_city',
            'contact_country_id',
            'firstname',
            'middlename',
            'lastname'
        ]
        self.env['ir.model.fields'].formbuilder_whitelist('hr.applicant', field_list)


    @api.onchange(
        'firstname',
        'middlename',
        'lastname'
    )
    def onchange_name_params(self):
        name_list = [self.lastname or '', self.firstname or '', self.middlename or '']
        name = ' '.join(name_list)
        self.update({'partner_name': name})

    @api.multi
    def write(self, values):
        res = super(HrApplicant, self).write(values)
        if values.get('emp_id', False):
            for applicant in self:
                work_partner_id = self.env['res.partner'].sudo().search(
                    [('name', 'ilike', applicant.work_employer)], limit=1
                )
                write_vals = {
                    'birthday': applicant.birthday,
                    'gender': applicant.gender,
                    'marital': applicant.marital,
                    'children': applicant.children,
                }
                if applicant.work_position:
                    work_exp_values = {
                        'start_date': applicant.work_start_date,
                        'end_date': applicant.work_end_date,
                        'work_supervisor': applicant.work_supervisor,
                        'work_contact_number': applicant.work_contact_number,
                        'name': applicant.work_position,
                        'partner_id': work_partner_id.id
                    }
                    write_vals.update({'experience_ids': [(0, 0, work_exp_values)],})

                if applicant.edu_coursename:
                    edu_values = {
                        'name': applicant.edu_coursename,
                        'edu_schoolname': applicant.edu_schoolname,
                        'edu_graduate_year': applicant.edu_graduate_year,
                        'edu_level_year': applicant.edu_level_year
                    }
                    write_vals.update({'academic_ids': [(0, 0, edu_values)],})

                applicant.emp_id.write(write_vals)
                
                if applicant.emp_id.address_home_id:
                    street2 = applicant.contact_zone or ''
                    applicant.emp_id.address_home_id.write({
                        'street': applicant.contact_street,
                        'street2': street2,
                        'city': applicant.contact_city,
                        'country_id': applicant.contact_country_id.id,
                        'zip': applicant.contact_zip,
                    })

        return res
