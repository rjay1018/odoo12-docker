from odoo import models, api

class SettlementSummaryPartnerProductReport(models.AbstractModel):
    _name = 'report.sale_commission_extended.summary_partner_prod'
    _description = 'Settlement Summary Partner Product Report'

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
        grouped_analytics = {}
        all_lines = list(settlement.lines)
        if hasattr(settlement, 'categ_lines'):
            all_lines += list(settlement.categ_lines)

        for line in all_lines:
            analytic = line.invoice_line.account_analytic_id
            partner = line.invoice.partner_id
            product = line.invoice_line.product_id
            invoice = line.invoice
            inv_line_id = line.invoice_line.id

            # First level: Analytic Account
            a_key = analytic.id if analytic else False
            if a_key not in grouped_analytics:
                grouped_analytics[a_key] = {
                    'analytic': analytic.name if analytic else 'No Analytic Account',
                    'partners_dict': {},
                    'total_price': 0.0,
                    'total_amount': 0.0,
                }

            a_dict = grouped_analytics[a_key]

            # Second level: Partner
            p_key = partner.id if partner else False
            if p_key not in a_dict['partners_dict']:
                a_dict['partners_dict'][p_key] = {
                    'partner': partner.name if partner else 'No Partner',
                    'lines_dict': {},
                    'total_price': 0.0,
                    'total_amount': 0.0,
                }

            p_dict = a_dict['partners_dict'][p_key]

            # Line level
            l_key = (invoice.id if invoice else False, product.id if product else False)
            if l_key not in p_dict['lines_dict']:
                inv_name = invoice.name if invoice and invoice.name else (invoice.number if invoice else 'No Invoice')
                p_dict['lines_dict'][l_key] = {
                    'invoice': inv_name,
                    'product': product.name if product else 'No Product',
                    'uom': line.invoice_line.uom_id.name if line.invoice_line.uom_id else '',
                    'quantity': line.invoice_line.quantity,
                    'unit_price': line.invoice_line.price_unit,
                    'price_subtotal': 0.0,
                    'amount_subtotal': 0.0,
                    '_processed_inv_lines': set(),
                }

            l_dict = p_dict['lines_dict'][l_key]

            if inv_line_id not in l_dict['_processed_inv_lines']:
                price = line.invoice_line.price_subtotal
                l_dict['price_subtotal'] += price
                p_dict['total_price'] += price
                a_dict['total_price'] += price
                l_dict['_processed_inv_lines'].add(inv_line_id)

            amount = line.settled_amount
            l_dict['amount_subtotal'] += amount
            p_dict['total_amount'] += amount
            a_dict['total_amount'] += amount

        # Sort and flatten
        result = list(grouped_analytics.values())
        result.sort(key=lambda x: x['analytic'])
        for a in result:
            a['partners'] = list(a['partners_dict'].values())
            a['partners'].sort(key=lambda x: x['partner'])
            for p in a['partners']:
                p['lines'] = list(p['lines_dict'].values())
                p['lines'].sort(key=lambda x: (x['invoice'], x['product']))

        return result

