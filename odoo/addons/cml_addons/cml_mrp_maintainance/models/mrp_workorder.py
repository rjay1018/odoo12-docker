from odoo import fields, models, api, _


class MrpWorkCenter(models.Model):
    _inherit = 'mrp.workcenter'

    equipment_id = fields.Many2one(
        'maintenance.equipment',
        store=True
    )


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    equipment_id = fields.Many2one(
        'maintenance.equipment',
        related='workcenter_id.equipment_id',
        store=True
    )

    @api.multi
    def maintenance_request(self):
        return {
            'name': _('Maintenance Request'),
            'domain': [('equipment_id', '=', self.equipment_id)],
            'view_type': 'form',
            'res_model': 'maintenance.request',
            'view_id': False,
            'view_mode': 'form,tree',
            'type': 'ir.actions.act_window',
        }

