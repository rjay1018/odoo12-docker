# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class product_template(models.Model):

    _inherit = 'product.template'

    is_equipment_product = fields.Boolean(
        string="Is Equipment Product?",
        copy=False
    )


class maintenance_extensions(models.Model):

    _inherit = 'maintenance.equipment'


    usage_type = fields.Selection([
              ('equipment', 'Equipment'),
              ('spare_Part', 'Spare Part'),
         ], default='equipment', string="Usage"
    )

    related_product_id = fields.Many2one(
        'product.product',
        string="Related Product"
    )

    spare_part_id = fields.One2many(
        'maintenance.equipment', 'maintenance_equipment_id',
    )

    maintenance_equipment_id = fields.Many2one(
        'maintenance.equipment'
    )
    asset_id = fields.Many2one(
        'account.asset.asset',
        readonly=True
    )

    checklist_id = fields.Many2many(
        'equipment.checklist',
        string="Checklist",
    )

    @api.multi
    def request_button(self):
        act = self.env.ref('maintenance.hr_equipment_request_action').read([])[0]
        act['domain'] = [('equipment_id', '=', self.id)]
        return act

    @api.constrains('related_product_id')
    def check_loan(self):
        if not(self.related_product_id):
            raise ValidationError("Please set related product!")

    def action_open_purchase_orders(self):
        act = self.env.ref('purchase.purchase_form_action').read([])[0]
        maintenance_req_ids = self.env['maintenance.request'].sudo().search(
            [('equipment_id', '=', self.id)]
        )
        po_ids = self.env['purchase.order'].sudo().search(
            [('maintenance_request_id', 'in', maintenance_req_ids.ids)]
        ).ids
        act['domain'] = [('id', 'in', po_ids)]
        return act


class equipment_checklist(models.Model):
    _name = 'equipment.checklist'

    name = fields.Char(
        required=True,
        string="Name"
    )
