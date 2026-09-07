# -*- coding: utf-8 -*-


from odoo import models, api, fields


class MrpManufactureProcess(models.Model):
    _inherit = 'product.category'

    account_labour_cost_id = fields.Many2one(
        'account.account',
        string='Account Labour Cost',
        domain="[('deprecated', '=', False)]",
    )
    account_overhead_cost_id = fields.Many2one(
        'account.account',
        string='Account Overhead Cost',
        domain="[('deprecated', '=', False)]",
    )
    account_cost_id = fields.Many2one(
        'account.account',
        string='Account Cost',
        domain="[('deprecated', '=', False)]",
    )
    cost_from_mo = fields.Boolean(
        string="Cost based on latest MO"
    )
    
    
