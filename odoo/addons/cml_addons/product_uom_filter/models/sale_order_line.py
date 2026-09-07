# -*- coding: utf-8 -*-
# Part of Kiran Infosoft. See LICENSE file for full copyright and licensing details.

from odoo import fields,api,models, _
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError


class sale_order_line(models.Model):

	_inherit = "sale.order.line"

	uom_ids = fields.Many2many(
		"uom.uom",
		string="UOM IDs",
	)

	@api.onchange('product_id')
	def product_id_change(self):
		res = super(sale_order_line,self).product_id_change()
		if self.product_id:
			uom_id_list = self.product_id.uom_ids.ids
			default_product_uom_id = self.product_id.uom_id.id
			if default_product_uom_id not in uom_id_list:
				uom_id_list.append(default_product_uom_id)
			self.uom_ids = self.env['uom.uom'].browse(uom_id_list)
			res['domain']['product_uom'] = [('id', 'in', uom_id_list)]
		return res

	@api.multi
	def _action_launch_stock_rule(self):
		"""
		Launch procurement group run method with required/custom fields genrated by a
		sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
		depending on the sale order line product rule.
		"""
		precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
		errors = []
		for line in self:
			if line.state != 'sale' or not line.product_id.type in ('consu','product'):
				continue
			qty = line._get_qty_procurement()
			if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
				continue

			group_id = line.order_id.procurement_group_id
			if not group_id:
				group_id = self.env['procurement.group'].create({
					'name': line.order_id.name, 'move_type': line.order_id.picking_policy,
					'sale_id': line.order_id.id,
					'partner_id': line.order_id.partner_shipping_id.id,
				})
				line.order_id.procurement_group_id = group_id
			else:
				# In case the procurement group is already created and the order was
				# cancelled, we need to update certain values of the group.
				updated_vals = {}
				if group_id.partner_id != line.order_id.partner_shipping_id:
					updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
				if group_id.move_type != line.order_id.picking_policy:
					updated_vals.update({'move_type': line.order_id.picking_policy})
				if updated_vals:
					group_id.write(updated_vals)

			values = line._prepare_procurement_values(group_id=group_id)
			product_qty = line.product_uom_qty - qty

			procurement_uom = line.product_uom
			quant_uom = line.product_id.uom_id
			get_param = self.env['ir.config_parameter'].sudo().get_param
			if procurement_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
				product_qty = line.product_uom._compute_quantity(product_qty, quant_uom, rounding_method='HALF-UP')
				procurement_uom = quant_uom

			try:
				self.env['procurement.group'].run(line.product_id, line.product_uom_qty, line.product_uom, line.order_id.partner_shipping_id.property_stock_customer, line.name, line.order_id.name, values)
			except UserError as error:
				errors.append(error.name)
		if errors:
			raise UserError('\n'.join(errors))
		return True