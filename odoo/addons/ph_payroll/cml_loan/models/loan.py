from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Loan(models.Model):
    _inherit = 'hr.loan'

    STATE = [
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('noted', 'Noted'),
        ('for_approval', 'Recommending Approval'),
        ('approve', 'Approved'),
        ('cancel', 'Cancelled')
    ]

    state = fields.Selection(STATE, string='State', default='draft', track_visibility='onchange', copy=False)

    def _loan_validation(self):
        if self.loan_amount <= 0 or self.monthly_payment <= 0:
            raise ValidationError(_('Loan Amount or Payment per Period must not be zero'))

        if self.monthly_payment > self.loan_amount:
            raise ValidationError(_('Payment per Period must be equal or less than loanable amount'))

    def action_noted(self):
        self._loan_validation()
        self.state = 'noted'

    def action_for_approval(self):
        self._loan_validation()
        self.state = 'for_approval'

