# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SpecialistTags(models.Model):

    _name = "specialist.availability"
    _description = "Availability Tags"
 
    employee_ids = fields.Many2many('hr.employee', 'specialist_availability_rel', 'availability_id', 'emp_id', string='Specialist')
    name = fields.Char(string="Name", required=True)
    color = fields.Integer(string='Color Index')
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]


class SpecialistSpecialty(models.Model):
    _name = 'specialty.tags'
    _description = "Specialist Forte or Speciality"

    name = fields.Char(
        string='Name',
    )
    color = fields.Integer(
        string='Color Index',
    )
    employee_ids = fields.Many2many('hr.employee', 'specialist_speciality_rel', 'specialty_tags', 'emp_id', string='Specialist')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]