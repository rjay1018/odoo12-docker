import datetime
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Employeecontract_changes_hrisECOLA(models.Model):
    _inherit = 'hr.contract'

    days_year= fields.Selection([('1', '261'),
                                    ('2', '313'),
                                    ('3', '365'),
                                    ('4', '392.5')
                                    ], string="Days in a Year")

    travel_reimbursement_amount = fields.Monetary(string='Travel Allowance',
                                               track_visibility='onchange',
                                               readonly=True,
                                               states={'draft': [('readonly', False)]},
                                               help='The Reimbursement of travel expenses for the employee')

    ecola = fields.Monetary(string='ECOLA',
                                     readonly=True,
                                          states={'draft': [('readonly', False)]})
    leave_allo= fields.Float(string='Leave',
                                     track_visibility='onchange',
                                     readonly=True,
                                          states={'draft': [('readonly', False)]})
