from odoo import models, fields, api, tools
import xlwt
import base64
from io import BytesIO
from datetime import date, datetime
from dateutil import relativedelta

class PaymentReport(models.TransientModel):
    _name = "payment.report.wizard"
    _description = "Payment Report Wizard"

    payment_start_date = fields.Date(
        string="Payment Start",
        default=lambda self: date.today().replace(day=1),
        required=True
    )

    payment_end_date = fields.Date(
        string="Payment End",
        default=lambda self: (date.today().replace(day=1) + relativedelta.relativedelta(months=1, days=-1)),
        required=True
    )

    journal_id = fields.Many2one(
        'account.journal',
        string='Journal'
    )

    def export_payment_xls(self):
        """Generate and return an Excel report for payments."""
        filename = "Payment Report.xls"
        workbook = xlwt.Workbook(encoding='utf-8')
        sheet = workbook.add_sheet('sheet1')

        # Set column widths
        for col in range(11):
            sheet.col(col).width = 6500

        # Define custom color for gray
        xlwt.add_palette_colour("gray_ega", 0x21)
        workbook.set_colour_RGB(0x21, 168, 230, 217)

        # Define cell formats
        format5 = xlwt.easyxf("align: horiz center;font: height 350,bold 1, color black;")
        format66 = xlwt.easyxf("align: horiz center;font: bold 1, color black;pattern: pattern solid, fore_colour gray_ega;borders: top thin, bottom thin, left thin, right thin;")
        row_format = xlwt.easyxf("align: horiz left;borders: top thin, bottom thin, left thin, right thin;")
        row_date_format = xlwt.easyxf("align: horiz left;borders: top thin, bottom thin, left thin, right thin;", num_format_str='DD-MM-YYYY')
        qty_format = xlwt.easyxf("align: horiz right;borders: top thin, bottom thin, left thin, right thin;", num_format_str='#,##0.00')
        index_format = xlwt.easyxf("align: horiz center;borders: top thin, bottom thin, left thin, right thin;")
        amount_format = xlwt.easyxf("align: horiz right;font: bold 1, color black;borders: top thin, bottom thin, left thin, right thin;", num_format_str='#,##0.00')
        negative_amount_format = xlwt.easyxf("align: horiz right;font: bold 1, color red;borders: top thin, bottom thin, left thin, right thin;", num_format_str='#,##0.00')

        # Write headers
        sheet.write_merge(0, 1, 0, 10, 'Payment Reporting', format5)
        headers = ['NO', 'NAME', 'PARTNER', 'CHEQUE NUMBER', 'CHEQUE DATE', 'JOURNAL', 'MOVE NAME', 'COMMUNICATION', 'PAYMENT DATE', 'AMOUNT', 'RUNNING BALANCE']
        for col, header in enumerate(headers):
            sheet.write(3, col, header, format66)

        # Define domain for filtering payments
        domain = [('payment_date', '>=', self.payment_start_date),
                ('payment_date', '<=', self.payment_end_date)]
        if self.journal_id:
            domain += [('journal_id', '=', self.journal_id.id)]

        # Fetch payments
        account_payments = self.env['account.payment'].search(domain)

        # Raise error if no payments are found
        if not account_payments:
            raise UserError("No payments found for the selected criteria.")

        # Initialize variables
        row = 4
        number = 0
        total_amount = 0
        running_balance = 0

        # Iterate through payments
        for payment in account_payments:
            number += 1

            # Determine amount based on payment_type
            if payment.payment_type == 'outbound':
                amount = -payment.amount  # Negative for outbound payments
            else:
                amount = payment.amount  # Positive for all other payment types

            # Update running balance
            running_balance += amount

            # Choose red color format if amount is negative
            amount_style = negative_amount_format if amount < 0 else qty_format
            balance_style = negative_amount_format if running_balance < 0 else qty_format

            # Write payment details to the sheet
            sheet.write(row, 0, number, index_format)
            sheet.write(row, 1, payment.name or "N/A", row_format)
            sheet.write(row, 2, payment.partner_id.name or "N/A", row_format)
            sheet.write(row, 3, payment.cheque_no or "N/A", row_format)
            sheet.write(row, 4, payment.cheque_date or "N/A", row_date_format)
            sheet.write(row, 5, payment.journal_id.name or "N/A", row_format)
            sheet.write(row, 6, payment.move_name or "N/A", row_format)
            sheet.write(row, 7, payment.communication or "N/A", row_format)
            sheet.write(row, 8, payment.payment_date or "", row_date_format)
            sheet.write(row, 9, amount, amount_style)
            sheet.write(row, 10, running_balance, balance_style)

            total_amount += amount
            row += 1

        # Write total row
        sheet.write(row, 0, 'Total', format66)
        sheet.write(row, 9, total_amount, amount_format)
        sheet.write(row, 10, running_balance, amount_format)

        # Save and return the Excel file
        stream = BytesIO()
        workbook.save(stream)
        out = base64.encodebytes(stream.getvalue())
        exel_id = self.env['payment.reports.excel'].create({'file_name': filename, 'excel_file': out})
        return {
            'view_mode': 'form',
            'res_id': exel_id.id,
            'res_model': 'payment.reports.excel',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
        
class PaymentExcelReport(models.TransientModel):
    _name = "payment.reports.excel"
    _description = "Payment Report Excel"

    file_name = fields.Char('Excel File', readonly=True)
    excel_file = fields.Binary('Download Report', readonly=True)
