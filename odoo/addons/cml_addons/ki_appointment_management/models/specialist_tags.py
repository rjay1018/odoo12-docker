# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SpecialistTags(models.Model):

    _inherit = "specialist.availability"

    time = fields.Float(
        string='Time'
    )