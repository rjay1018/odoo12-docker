import io
import xlwt
from odoo import http
from odoo.http import request
from ..reports.commission_report_data import (
    get_by_customer_data,
    get_by_invoice_data,
)


class CommissionSettlementExport(http.Controller):

    @http.route('/sale_commission_extended/export_excel/<int:settlement_id>', type='http', auth='user')
    def export_excel(self, settlement_id, **kw):
        settlement = request.env['sale.commission.settlement'].browse(settlement_id)
        if not settlement.exists():
            return request.not_found()

        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('Commission Summary')

        # Styles
        header_style = xlwt.easyxf('font: bold on; align: horiz center')
        bold_style = xlwt.easyxf('font: bold on')
        money_style = xlwt.easyxf(num_format_str='#,##0.00')

        # Header Information
        worksheet.write(0, 0, 'Name of Agent:', bold_style)
        worksheet.write(0, 1, settlement.agent.name or '')

        worksheet.write(1, 0, 'Commission Coverage Date:', bold_style)
        date_range = '%s to %s' % (
            settlement.date_from.strftime('%Y-%m-%d') if settlement.date_from else '',
            settlement.date_to.strftime('%Y-%m-%d') if settlement.date_to else ''
        )
        worksheet.write(1, 1, date_range)

        # Table Headers
        headers = [
            'Product item',
            'Invoice Number',
            'Invoice Date',
            'UoM',
            'Quantity',
            'Unit Price',
            'Commission Type',
            'Based Amount of Commission',
            'Commission Total'
        ]
        
        row = 3
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, header_style)
            # Adjust column width (1 character is approx 256)
            worksheet.col(col).width = 6000

        # Data Rows
        row += 1
        total_commission = 0.0
        export_data = []

        # Collect partner category lines (agent_line)
        for s_line in settlement.lines:
            for a_line in s_line.agent_line:
                product_name = a_line.object_id.product_id.name or ''
                inv_number = a_line.object_id.invoice_id.number or ''
                date_inv = a_line.object_id.invoice_id.date_invoice
                inv_date = date_inv.strftime('%Y-%m-%d') if date_inv else ''
                comm_type = a_line.commission.name or ''

                base_amount = a_line.object_id.price_subtotal

                comm_total = a_line.amount
                total_commission += comm_total

                export_data.append({
                    'product': product_name,
                    'invoice': inv_number,
                    'invoice_date': inv_date,
                    'uom': a_line.object_id.uom_id.name or '',
                    'qty': a_line.object_id.quantity,
                    'unit_price': a_line.object_id.price_unit,
                    'type': comm_type,
                    'base': base_amount,
                    'total': comm_total
                })

        # Collect product category lines
        for c_line in settlement.categ_lines:
            for a_line in c_line.agent_line_categ:
                product_name = a_line.object_id.product_id.name or ''
                inv_number = a_line.object_id.invoice_id.number or ''
                date_inv = a_line.object_id.invoice_id.date_invoice
                inv_date = date_inv.strftime('%Y-%m-%d') if date_inv else ''
                comm_type = a_line.commission.name or ''

                base_amount = a_line.object_id.price_subtotal

                comm_total = a_line.amount
                total_commission += comm_total

                export_data.append({
                    'product': product_name,
                    'invoice': inv_number,
                    'invoice_date': inv_date,
                    'uom': a_line.object_id.uom_id.name or '',
                    'qty': a_line.object_id.quantity,
                    'unit_price': a_line.object_id.price_unit,
                    'type': comm_type,
                    'base': base_amount,
                    'total': comm_total
                })

        # Sort by product, then invoice, then unit price (free lines first)
        export_data.sort(key=lambda x: (
            x['product'].lower() if x['product'] else '',
            x['invoice'],
            x['unit_price'],
        ))

        # Write data to worksheet
        for data in export_data:
            worksheet.write(row, 0, data['product'])
            worksheet.write(row, 1, data['invoice'])
            worksheet.write(row, 2, data['invoice_date'])
            worksheet.write(row, 3, data['uom'])
            worksheet.write(row, 4, data['qty'], money_style)
            worksheet.write(row, 5, data['unit_price'], money_style)
            worksheet.write(row, 6, data['type'])
            worksheet.write(row, 7, data['base'], money_style)
            worksheet.write(row, 8, data['total'], money_style)
            row += 1

        # Footer
        row += 1
        worksheet.write(row, 7, 'Total Commission:', bold_style)
        worksheet.write(row, 8, total_commission, money_style)

        fp = io.BytesIO()
        workbook.save(fp)
        fp.seek(0)
        xls_data = fp.read()

        agent_name_safe = (settlement.agent.name or 'Agent').replace(' ', '_')
        filename = 'Commission_Summary_%s.xls' % agent_name_safe

        return request.make_response(xls_data, headers=[
            ('Content-Type', 'application/vnd.ms-excel'),
            ('Content-Disposition', 'attachment; filename="%s"' % filename)
        ])

    def _xls_styles(self):
        return {
            'header': xlwt.easyxf('font: bold on; align: horiz center; pattern: pattern solid, fore_colour gray25;'),
            'group': xlwt.easyxf('font: bold on; pattern: pattern solid, fore_colour ice_blue;'),
            'bold': xlwt.easyxf('font: bold on;'),
            'bold_right': xlwt.easyxf('font: bold on; align: horiz right;'),
            'money': xlwt.easyxf(num_format_str='#,##0.00'),
            'bold_money': xlwt.easyxf('font: bold on;', num_format_str='#,##0.00'),
            'right': xlwt.easyxf('align: horiz right;'),
        }

    def _write_settlement_header(self, ws, settlement, title, styles):
        ws.write(0, 0, title, styles['bold'])
        ws.write(1, 0, 'Sales Agent:', styles['bold'])
        ws.write(1, 1, settlement.agent.name or '')
        ws.write(2, 0, 'Period:', styles['bold'])
        date_range = '%s to %s' % (
            settlement.date_from.strftime('%Y-%m-%d') if settlement.date_from else '',
            settlement.date_to.strftime('%Y-%m-%d') if settlement.date_to else '',
        )
        ws.write(2, 1, date_range)

    def _workbook_to_response(self, workbook, filename):
        fp = io.BytesIO()
        workbook.save(fp)
        fp.seek(0)
        return request.make_response(fp.read(), headers=[
            ('Content-Type', 'application/vnd.ms-excel'),
            ('Content-Disposition', 'attachment; filename="%s"' % filename),
        ])

    @http.route('/sale_commission_extended/export_by_customer/<int:settlement_id>', type='http', auth='user')
    def export_excel_by_customer(self, settlement_id, **kw):
        settlement = request.env['sale.commission.settlement'].browse(settlement_id)
        if not settlement.exists():
            return request.not_found()

        workbook = xlwt.Workbook(encoding='utf-8')
        ws = workbook.add_sheet('Commission By Customer')
        styles = self._xls_styles()
        self._write_settlement_header(ws, settlement, 'Commission Report by Customer', styles)

        headers = [
            'Invoice #', 'Date', 'Product', 'Qty',
            'Price', 'Total', 'Comm. Rate', 'Comm. Amount',
        ]
        widths = [5000, 3500, 9000, 3200, 3800, 4500, 3800, 4500]
        row = 4
        for col, (h, w) in enumerate(zip(headers, widths)):
            ws.write(row, col, h, styles['header'])
            ws.col(col).width = w

        data = get_by_customer_data(settlement)
        row += 1
        for cust in data['customers']:
            ws.write_merge(row, row, 0, 7, cust['partner'], styles['group'])
            row += 1
            for l in cust['lines']:
                ws.write(row, 0, l['invoice'])
                ws.write(row, 1, l['invoice_date'])
                ws.write(row, 2, l['product'])
                ws.write(row, 3, l['quantity'], styles['money'])
                ws.write(row, 4, l['unit_price'], styles['money'])
                ws.write(row, 5, l['price_subtotal'], styles['money'])
                ws.write(row, 6, l['commission_rate'], styles['right'])
                ws.write(row, 7, l['commission_amount'], styles['money'])
                row += 1
            ws.write_merge(row, row, 0, 4, 'Customer Subtotal:', styles['bold_right'])
            ws.write(row, 5, cust['total_sales'], styles['bold_money'])
            ws.write(row, 7, cust['total_commission'], styles['bold_money'])
            row += 1

        row += 1
        ws.write_merge(row, row, 0, 4, 'Grand Total:', styles['bold_right'])
        ws.write(row, 5, data['grand_total_sales'], styles['bold_money'])
        ws.write(row, 7, data['grand_total_commission'], styles['bold_money'])

        agent_safe = (settlement.agent.name or 'Agent').replace(' ', '_')
        return self._workbook_to_response(workbook, 'Commission_By_Customer_%s.xls' % agent_safe)

    @http.route('/sale_commission_extended/export_by_invoice/<int:settlement_id>', type='http', auth='user')
    def export_excel_by_invoice(self, settlement_id, **kw):
        settlement = request.env['sale.commission.settlement'].browse(settlement_id)
        if not settlement.exists():
            return request.not_found()

        workbook = xlwt.Workbook(encoding='utf-8')
        ws = workbook.add_sheet('Commission By Invoice')
        styles = self._xls_styles()
        self._write_settlement_header(ws, settlement, 'Commission Report by Invoice', styles)

        headers = ['Product', 'Qty', 'Price', 'Total', 'Comm. Rate', 'Comm. Amount']
        widths = [10000, 3200, 3800, 4500, 3800, 4500]
        row = 4
        for col, (h, w) in enumerate(zip(headers, widths)):
            ws.write(row, col, h, styles['header'])
            ws.col(col).width = w

        data = get_by_invoice_data(settlement)
        row += 1
        for inv in data['invoices']:
            banner = 'Invoice: %s | Customer: %s | Date: %s | Agent: %s' % (
                inv['invoice'], inv['partner'], inv['invoice_date'], inv['agent']
            )
            ws.write_merge(row, row, 0, 5, banner, styles['group'])
            row += 1
            for l in inv['lines']:
                ws.write(row, 0, l['product'])
                ws.write(row, 1, l['quantity'], styles['money'])
                ws.write(row, 2, l['unit_price'], styles['money'])
                ws.write(row, 3, l['price_subtotal'], styles['money'])
                ws.write(row, 4, l['commission_rate'], styles['right'])
                ws.write(row, 5, l['commission_amount'], styles['money'])
                row += 1
            ws.write_merge(row, row, 0, 2, 'Invoice Subtotal:', styles['bold_right'])
            ws.write(row, 3, inv['total_sales'], styles['bold_money'])
            ws.write(row, 5, inv['total_commission'], styles['bold_money'])
            row += 1

        row += 1
        ws.write_merge(row, row, 0, 2, 'Grand Total:', styles['bold_right'])
        ws.write(row, 3, data['grand_total_sales'], styles['bold_money'])
        ws.write(row, 5, data['grand_total_commission'], styles['bold_money'])

        agent_safe = (settlement.agent.name or 'Agent').replace(' ', '_')
        return self._workbook_to_response(workbook, 'Commission_By_Invoice_%s.xls' % agent_safe)

    @http.route('/sale_commission_extended/export_sales_performance/<int:wizard_id>', type='http', auth='user')
    def export_sales_performance(self, wizard_id, **kw):
        wizard = request.env['sale.commission.sales.performance.wizard'].browse(wizard_id)
        if not wizard.exists():
            return request.not_found()

        rdata = wizard.get_report_data()
        s = rdata['summary']
        month_cols = rdata['month_columns']

        workbook = xlwt.Workbook(encoding='utf-8')
        ws = workbook.add_sheet('Sales Performance')
        styles = self._xls_styles()
        pct_style = xlwt.easyxf(num_format_str='0.00"%"')
        warn_money = xlwt.easyxf(
            'pattern: pattern solid, fore_colour light_yellow;',
            num_format_str='#,##0.00',
        )

        # Top Summary Block
        ws.write(0, 0, 'Sales Performance Report vs. Wholesale Price', styles['bold'])
        ws.write(1, 0, 'Agent:', styles['bold'])
        ws.write(1, 1, s['agent'])
        ws.write(1, 3, 'Commission Total:', styles['bold'])
        ws.write(1, 4, s['commission_total'], styles['bold_money'])

        ws.write(2, 0, 'Period:', styles['bold'])
        ws.write(2, 1, s['period'])
        ws.write(2, 3, 'Commission Paid:', styles['bold'])
        ws.write(2, 4, s['commission_paid'], styles['money'])

        ws.write(3, 0, 'Total Amount:', styles['bold'])
        ws.write(3, 1, s['total_amount'], styles['bold_money'])
        ws.write(3, 3, 'Commission Unpaid:', styles['bold'])
        ws.write(3, 4, s['commission_unpaid'], styles['money'])

        ws.write(4, 3, 'Above BM / Below BM / No Sale:', styles['bold'])
        ws.write(4, 4, '%d / %d / %d' % (s['above_bm_count'], s['below_bm_count'], s['no_sale_count']))

        ws.write(5, 3, 'Above BM Rate:', styles['bold'])
        ws.write(5, 4, s['above_bm_rate'], pct_style)

        ws.write(6, 3, 'Quota Pass / Fail / N/A:', styles['bold'])
        ws.write(6, 4, '%d / %d / %d' % (s['quota_pass_count'], s['quota_fail_count'], s['quota_na_count']))

        # Dynamic Product Category Totals (left column)
        cat_row = 4
        for cat in s['category_totals']:
            ws.write(cat_row, 0, cat['category'])
            ws.write(cat_row, 1, cat['amount'], styles['money'])
            cat_row += 1

        # Item Table Header
        row = max(cat_row, 7) + 1
        headers = ['Item', 'UoM', 'Total Qty']
        headers.extend([label for _, label in month_cols])
        headers.extend([
            'Sub Total Amount', 'Commi %', 'Commission Amount',
            'Avg Selling Price', 'Whole Sale Price', 'Evaluation',
            'Quota', 'Realization',
        ])
        for col, h in enumerate(headers):
            ws.write(row, col, h, styles['header'])
            ws.col(col).width = 10000 if col == 0 else 4000

        # Item Rows
        row += 1
        for r in rdata['rows']:
            col = 0
            ws.write(row, col, r['item']); col += 1
            ws.write(row, col, r['uom']); col += 1
            ws.write(row, col, r['total_qty'], styles['money']); col += 1
            for mq in r['month_qtys']:
                ws.write(row, col, mq, styles['money']); col += 1
            ws.write(row, col, r['subtotal_amount'], styles['money']); col += 1
            ws.write(row, col, r['comm_rate'], styles['right']); col += 1
            ws.write(row, col, r['commission_amount'], styles['money']); col += 1
            ws.write(row, col, r['avg_selling_price'], styles['money']); col += 1
            ws.write(
                row, col, r['wholesale_price'],
                warn_money if r['missing_wholesale_price'] else styles['money'],
            ); col += 1
            ws.write(row, col, r['evaluation']); col += 1
            if r['quota'] is not None:
                ws.write(row, col, r['quota'], styles['money'])
            else:
                ws.write(row, col, 'N/A', styles['right'])
            col += 1
            if r['realization'] is not None:
                ws.write(row, col, r['realization'], pct_style)
            else:
                ws.write(row, col, 'N/A', styles['right'])
            row += 1

        agent_safe = (s['agent'] or 'Agent').replace(' ', '_')
        period_safe = (s['period'] or 'Period').replace(' ', '_')
        filename = 'Sales_Performance_%s_%s.xls' % (agent_safe, period_safe)
        return self._workbook_to_response(workbook, filename)
