# -*- coding: utf-8 -*-

from odoo import models, fields, api


class equipment_checklist(models.Model):

    _name ='equipment.checklist.result'

    request_id = fields.Many2one('maintenance.request')
    checklist_id = fields.Many2one(
        'equipment.checklist'
    )
    is_pass = fields.Boolean(
    )


class maintenance_spare_parts(models.Model):
    _name = 'maintenance.spare.parts'

    part_id = fields.Many2one('maintenance.request')

    spare_part_id = fields.Many2one(
        'maintenance.equipment',
    )
    price = fields.Float(
        string="Price"
    )
    quantity = fields.Float(
        string="Quantity"
    )
    po_line_id = fields.Many2one(
        'purchase.order.line',
        string="PO Line",
        copy=False,
        readonly=True
    )


class maintenance_request(models.Model):
    _inherit ='maintenance.request'

    checklist_result_id = fields.One2many(
        'equipment.checklist.result', 'request_id'
    )
    additional_spare_part_id = fields.One2many(
            'maintenance.spare.parts',
            'part_id'
    )

    @api.onchange('equipment_id')
    def on_change_set(self):
        checklist_id = []
        self.checklist_result_id = [(6, 0, [])]
        for i in self.equipment_id.checklist_id:
            checklist_id.append((0, 0, {'checklist_id': i.id}))
        self.checklist_result_id = checklist_id


