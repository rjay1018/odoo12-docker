# -*- coding: utf-8 -*-
# Part of Kiran Infosoft. See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class HrAcademic(models.Model):
    _inherit = 'hr.academic'

    edu_schoolname = fields.Char(
        string="School Name",
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


class HrExperience(models.Model):
    _inherit = 'hr.experience'

    work_supervisor = fields.Char(
        string="Supervisor",
        copy=False
    )
    work_contact_number = fields.Char(
        string="Contact Number",
        copy=False
    )
