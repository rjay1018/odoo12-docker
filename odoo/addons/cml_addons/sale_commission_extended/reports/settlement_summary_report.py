from odoo import models, api

class SettlementSummaryReport(models.AbstractModel):
    _name = 'report.sale_commission_extended.report_settlement_summary'
    _description = 'Settlement Summary Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.commission.settlement'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'sale.commission.settlement',
            'docs': docs,
            'get_grouped_lines': self._get_grouped_lines,
        }

    def _get_grouped_lines(self, settlement):
        grouped = {}
        all_lines = list(settlement.lines)
        if hasattr(settlement, 'categ_lines'):
            all_lines += list(settlement.categ_lines)
            
        for line in all_lines:
            analytic_account = line.invoice_line.account_analytic_id
            commission = line.commission
            inv_line_id = line.invoice_line.id
            
            key = (analytic_account.id if analytic_account else False, commission.id if commission else False)
            if key not in grouped:
                grouped[key] = {
                    'analytic_account': analytic_account.name if analytic_account else 'No Analytic Account',
                    'commission': commission.name if commission else 'No Commission',
                    'price_subtotal': 0.0,
                    'amount_subtotal': 0.0,
                    '_processed_inv_lines': set(),
                }
            
            if inv_line_id not in grouped[key]['_processed_inv_lines']:
                grouped[key]['price_subtotal'] += line.invoice_line.price_subtotal
                grouped[key]['_processed_inv_lines'].add(inv_line_id)
                
            grouped[key]['amount_subtotal'] += line.settled_amount
            
        result = list(grouped.values())
        result.sort(key=lambda x: (x['analytic_account'], x['commission']))
        return result
