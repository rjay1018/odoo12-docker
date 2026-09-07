from odoo import fields, models, api


class BatchPickingTripTicket(models.Model):
    _inherit = 'stock.picking.batch'

    fleet_id = fields.Many2one(
        string='Vehicle/Truck',
        comodel_name='fleet.vehicle',
        track_visibility="always",
        required=True
    )
    driver_id = fields.Many2one(
        string='Driver',
        related='fleet_id.driver_id'
    )
    helper_id = fields.Many2one(
        string='Helper',
        comodel_name='hr.employee'
    )
    calltime = fields.Float(
        string='Call Time'
    )

    odometer_value = fields.Float(
        string='Last Odometer Value',
        related = 'fleet_id.odometer'
    )

    odoometer_lines = fields.One2many(
        string='Odometer Logs',
        comodel_name='fleet.vehicle.odometer',
        inverse_name='batch_picking_id'
    )
