from odoo import models, fields, api


class equipment_asset(models.TransientModel):
    _name = "equipment.asset"

    equipment_asset_id = fields.Many2one(
        'account.asset.asset',
        string="Asset",
        required=True
    )

    @api.multi
    def submit_asset_record(self):
        active_ids = self.env.context.get('active_ids', [])
        active_equipment_record = self.env['maintenance.equipment'].browse(active_ids)
        active_equipment_record.asset_id = self.equipment_asset_id
        self.equipment_asset_id.maintenance_equipment_id =active_equipment_record.id
