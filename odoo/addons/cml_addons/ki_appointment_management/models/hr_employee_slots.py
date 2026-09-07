# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HrEmployeeSlots(models.Model):
    _name='hr.employee.slots'

    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee"
    )
    slot_id = fields.Many2one(
        'specialist.availability',
        string="Slot"
    )
    date = fields.Date(
        string = "Date"
    )