# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockScrap(models.Model):
    _name = "stock.scrap"
    _inherit = ['stock.scrap', 'tier.validation','mail.thread']
    _state_from = ['draft']
    _state_to = ['done']

