from odoo import fields, models, api


class FleetVehicleLogFuel(models.Model):
    _name = 'fleet.vehicle.log.fuel'
    _inherit = ['fleet.vehicle.log.fuel','mail.thread']

    attachment_ids = fields.Many2many('ir.attachment', string='Attachment')