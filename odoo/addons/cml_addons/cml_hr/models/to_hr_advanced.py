# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HRContractType(models.Model):
    _inherit = 'hr.contract.type'

    travel_reimbursement_percentage = fields.Float('Travel Allowance (%)')
    phone_reimbursement_percentage = fields.Float('Communication Allowance (%)')
    moving_allowance_percentage = fields.Float('Relocation Allowance (%)')
    harmful_subsidies_percentage = fields.Float('Hazard Pay (%)')
    responsibility_allowance_percentage = fields.Float('De Minimis (%)')
    hard_working_award_percentage = fields.Float('Longevity (%)')   

class HRContract(models.Model):
    _inherit = 'hr.contract'

    travel_reimbursement_amount = fields.Monetary('Travel Allowance')
    phone_reimbursement_amount = fields.Monetary('Communication Allowance')
    moving_allowance = fields.Monetary('Relocation Allowance')
    harmful_subsidies = fields.Monetary('Hazard Pay')
    responsibility_allowance = fields.Monetary('De Minimis')
    hard_working_award = fields.Monetary('Longevity')

    # cola = fields.Monetary('COLA')

class HRDepartment(models.Model):
    _inherit = 'hr.department'

    travel_reimbursement_amount = fields.Monetary('Travel Allowance')
    phone_reimbursement_amount = fields.Monetary('Communication Allowance')
    moving_allowance = fields.Monetary('Relocation Allowance')
    harmful_subsidies = fields.Monetary('Hazard Pay')
    responsibility_allowance = fields.Monetary('De Minimis')
    hard_working_award = fields.Monetary('Longevity')

class HRJob(models.Model):
    _inherit = 'hr.job'

    travel_reimbursement_amount = fields.Monetary('Travel Allowance')
    phone_reimbursement_amount = fields.Monetary('Communication Allowance')
    moving_allowance = fields.Monetary('Relocation Allowance')
    harmful_subsidies = fields.Monetary('Hazard Pay')
    responsibility_allowance = fields.Monetary('De Minimis')
    hard_working_award = fields.Monetary('Longevity')