# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class TimeSlot(models.Model):
    _name = 'clinic.timeslot'
    _description = 'Appointment Time Slots'

    name = fields.Char(
        string='Name',
        required=True     
    )
    timestart = fields.Float(
        string='Time Start',
    )
    timeend = fields.Float(
        string='Time End',
    )
    
    datesample = fields.Datetime(
        string='datesample',
        compute='_compute_field'  
    )

    # @api.depends('timeend')
    # def _compute_field(self):
    #     for record in self:
    #         record.datesample = (str(timedelta(hours=record.timeend)))
    
    @api.constrains('timestart','timeend')
    def _slot_validation(self):
        for rec in self:
            if rec.timestart < 00.00 or rec.timestart > 23.59 :
                raise ValidationError(('The Time Start value must be between 0:00 and 23:59!'))
        for rec in self:
            if rec.timeend < 00.00 or rec.timeend > 23.59 :
                raise ValidationError(('The Time End value must be between 0:00 and 23:59!'))

