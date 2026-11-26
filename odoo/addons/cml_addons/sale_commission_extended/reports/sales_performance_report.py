# -*- coding: utf-8 -*-
from odoo import api, models


class SalesPerformanceReport(models.AbstractModel):
    _name = 'report.sale_commission_extended.report_sales_performance'
    _description = 'Sales Performance Report vs. Wholesale Price'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.commission.sales.performance.wizard'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'sale.commission.sales.performance.wizard',
            'docs': docs,
        }
