# -*- coding: utf-8 -*-
# Part of Kiran Infosoft. See LICENSE file for full copyright and licensing details.

from odoo import fields,api,models
from odoo.tools.float_utils import float_compare

class purchase_order_line(models.Model):

	_inherit = "purchase.order.line"

	uom_ids = fields.Many2many(
		"uom.uom",
		string="UOM IDs",
	)

	@api.onchange('product_id')
	def onchange_product_id(self):
		res = super(purchase_order_line,self).onchange_product_id()
		if self.product_id:
			uom_id_list = self.product_id.uom_ids.ids
			default_product_uom_id = self.product_id.uom_id.id
			if default_product_uom_id not in uom_id_list:
				uom_id_list.append(default_product_uom_id)
			self.uom_ids = self.env['uom.uom'].browse(uom_id_list)
			res['domain']['product_uom'] = [('id', 'in', uom_id_list)]
		return res

	@api.multi
	def _prepare_stock_moves(self, picking):
		self.ensure_one()
		res = []
		if self.product_id.type not in ['product', 'consu']:
			return res
		qty = 0.0
		price_unit = self._get_stock_move_price_unit()
		for move in self.move_ids.filtered(lambda x: x.state != 'cancel' and not x.location_dest_id.usage == "supplier"):
			qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
		template = {
			# truncate to 2000 to avoid triggering index limit error
			# TODO: remove index in master?
			'name': (self.name or '')[:2000],
			'product_id': self.product_id.id,
			'product_uom': self.product_uom.id,
			'date': self.order_id.date_order,
			'date_expected': self.date_planned,
			'location_id': self.order_id.partner_id.property_stock_supplier.id,
			'location_dest_id': self.order_id._get_destination_location(),
			'picking_id': picking.id,
			'partner_id': self.order_id.dest_address_id.id,
			'move_dest_ids': [(4, x) for x in self.move_dest_ids.ids],
			'state': 'draft',
			'purchase_line_id': self.id,
			'company_id': self.order_id.company_id.id,
			'price_unit': price_unit,
			'picking_type_id': self.order_id.picking_type_id.id,
			'group_id': self.order_id.group_id.id,
			'origin': self.order_id.name,
			'route_ids': self.order_id.picking_type_id.warehouse_id and [(6, 0, [x.id for x in self.order_id.picking_type_id.warehouse_id.route_ids])] or [],
			'warehouse_id': self.order_id.picking_type_id.warehouse_id.id,
		}
		diff_quantity = self.product_qty - qty
		if float_compare(diff_quantity, 0.0,  precision_rounding=self.product_uom.rounding) > 0:
			quant_uom = self.product_id.uom_id
			get_param = self.env['ir.config_parameter'].sudo().get_param
			# Always call '_compute_quantity' to round the diff_quantity. Indeed, the PO quantity
			# is not rounded automatically following the UoM.
			if get_param('stock.propagate_uom') != '1':
				product_qty = self.product_uom._compute_quantity(diff_quantity, quant_uom, rounding_method='HALF-UP')
				template['product_uom'] = self.product_uom.id
				template['product_uom_qty'] = self.product_qty
			else:
				template['product_uom_qty'] = self.product_uom._compute_quantity(diff_quantity, self.product_uom, rounding_method='HALF-UP')
			res.append(template)
		return res