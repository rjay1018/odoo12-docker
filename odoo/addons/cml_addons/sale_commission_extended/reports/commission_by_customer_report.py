# -*- coding: utf-8 -*-
from odoo import api, models
from .commission_report_data import get_by_customer_data


class CommissionByCustomerReport(models.AbstractModel):
    _name = 'report.sale_commission_extended.report_commission_by_customer'
    _description = 'Commission Report by Customer'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.commission.settlement'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'sale.commission.settlement',
            'docs': docs,
            'get_by_customer_data': get_by_customer_data,
        }
