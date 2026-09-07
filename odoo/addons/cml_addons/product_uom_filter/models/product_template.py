# -*- coding: utf-8 -*-
# Part of Kiran Infosoft. See LICENSE file for full copyright and licensing details.

from odoo import fields,api,models

class product_template(models.Model):

	_inherit = "product.template"

	uom_ids = fields.Many2many(
		"uom.uom",
		string="UOM IDs",
	)

	uom_category_id = fields.Many2one(
		"uom.category",
		string="UOM Category",
		related='uom_id.category_id',
		store=True,
	)
