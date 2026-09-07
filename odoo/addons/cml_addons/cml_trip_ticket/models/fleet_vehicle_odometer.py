from odoo import fields, models, api


class OdometerExtend(models.Model):
    _inherit = 'fleet.vehicle.odometer'

    in_and_out = fields.Selection(
        string='Type',
        selection=[('departure', 'Departure'),
                   ('arrival', 'Arrival')]
    )
    timelogs = fields.Datetime(
        string="Log Time"
    )

    batch_picking_id = fields.Many2one('stock.picking.batch', string="Batch Picking ID")
