# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    image = fields.Binary('Photo')
