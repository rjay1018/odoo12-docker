# -*- coding: utf-8 -*-
# Part of Kiran Infosoft. See LICENSE file for full copyright and licensing details.

from odoo import fields,api,models

class product(models.Model):

	_inherit = "product.product"

	uom_ids = fields.Many2many(
		"uom.uom",
		string="UOM IDs",
	)