import io
import xlwt
from odoo import http
from odoo.http import request


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
                comm_type = a_line.commission.name or ''

                subtotal = a_line.object_id.price_subtotal
                if a_line.commission.amount_base_type == 'net_amount':
                    cost = a_line.object_id.product_id.standard_price * a_line.object_id.quantity
                    base_amount = max(0, subtotal - cost)
                else:
                    base_amount = subtotal

                comm_total = a_line.amount
                total_commission += comm_total

                export_data.append({
                    'product': product_name,
                    'invoice': inv_number,
                    'type': comm_type,
                    'base': base_amount,
                    'total': comm_total
                })

        # Collect product category lines
        for c_line in settlement.categ_lines:
            for a_line in c_line.agent_line_categ:
                product_name = a_line.object_id.product_id.name or ''
                inv_number = a_line.object_id.invoice_id.number or ''
                comm_type = a_line.commission.name or ''

                subtotal = a_line.object_id.price_subtotal
                if a_line.commission.amount_base_type == 'net_amount':
                    cost = a_line.object_id.product_id.standard_price * a_line.qty
                    base_amount = max(0, subtotal - cost)
                else:
                    base_amount = subtotal

                comm_total = a_line.amount
                total_commission += comm_total

                export_data.append({
                    'product': product_name,
                    'invoice': inv_number,
                    'type': comm_type,
                    'base': base_amount,
                    'total': comm_total
                })

        # Sort the data by product name
        export_data.sort(key=lambda x: x['product'].lower() if x['product'] else '')

        # Write data to worksheet
        for data in export_data:
            worksheet.write(row, 0, data['product'])
            worksheet.write(row, 1, data['invoice'])
            worksheet.write(row, 2, data['type'])
            worksheet.write(row, 3, data['base'], money_style)
            worksheet.write(row, 4, data['total'], money_style)
            row += 1

        # Footer
        row += 1
        worksheet.write(row, 3, 'Total Commission:', bold_style)
        worksheet.write(row, 4, total_commission, money_style)

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
