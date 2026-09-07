# -*- coding: utf-8 -*-
# Copyright 2017 Renato B. Lopez Jr. CML - Transformative Coaching and Consulting Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class AccountInvoice(models.Model):

    _inherit = "account.invoice"
    
    partner_category_id = fields.Many2many(
                string='Partner Tags',
                related="partner_id.category_id",
                readonly=True
    )
    