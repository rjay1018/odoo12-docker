# -*- coding: utf-8 -*-

from odoo import models, api


class WorkOrderCostCal(models.Model):
    _inherit = 'mrp.workcenter'

    @api.onchange('labour_costs_hour', 'overhead_cost_hour')
    def _onchange_invoice_date(self):
        self.costs_hour = self.labour_costs_hour + self.overhead_cost_hour