from odoo import models, fields, api, tools
import xlwt
import base64
from io import BytesIO
from datetime import date, datetime, timedelta
from dateutil import relativedelta


class ManufacturingReport(models.TransientModel):
    _name = "manufacturing.report.wizard"
    _description = "manufacturing Report "

    start_date = fields.Date(
        string="Start Date",
        default=datetime.now().strftime('%Y-%m-01'),
        required=True
    )

    end_date = fields.Date(
        string="End Date",
        default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
        required=True
    )

    def export_mrp_xls(self):
        filename = "Manufacturing Report.xls"
        workbook = xlwt.Workbook(encoding='utf-8')
        sheet = workbook.add_sheet('sheet1')

        sheet.col(0).width = 7000
        sheet.col(1).width = 7000
        sheet.col(2).width = 7000
        sheet.col(3).width = 7000
        sheet.col(4).width = 7000
        sheet.col(5).width = 7000
        sheet.col(7).width = 7000
        sheet.col(8).width = 9000

        format5 = xlwt.easyxf("align: horiz center;font: height 350,bold 1, color black;", num_format_str='DD/MM/YYYY')

        format6 = xlwt.easyxf("align: horiz center;font: bold 1, color black;borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin;", num_format_str='DD/MM/YYYY')

        format66 = xlwt.easyxf("align: horiz center;font: bold 1, color black;pattern: pattern solid, fore_colour gray_ega;borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin;", num_format_str='DD/MM/YYYY')

        format7 = xlwt.easyxf("align: horiz center;font: bold 1, color black;", num_format_str='DD/MM/YYYY')

        row_date_format = xlwt.easyxf("align: horiz right;font: bold 0, color black;borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin;", num_format_str='DD/MM/YYYY')
        row_format = xlwt.easyxf("align: horiz left;font: bold 0, color black;borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin;")

        qty_format = xlwt.easyxf("align: horiz right;font: bold 0, color black;borders: top_color black, bottom_color black, right_color black, left_color black,\
                                 left thin, right thin, top thin, bottom thin;")

        start_date = self.start_date.strftime('%d/%m/%Y')
        end_date = self.end_date.strftime('%d/%m/%Y')
        row_col = 4
        sheet.row(row_col).height = 380
        sheet.write_merge(0, 2, 0, 4, 'Manufacturing Reporting', format5)
        sheet.write(row_col, 0, 'Start Date', format6)
        sheet.write(row_col, 1, start_date, format7)
        sheet.write(row_col, 3, 'End Date', format6)
        sheet.write(row_col, 4, end_date, format7)

        sheet.write(7, 0, '#', format66)

        sheet.write(7, 1, 'MO #', format66)
        sheet.write(7, 2, 'Date', format66)
        sheet.write(7, 3, 'Item', format66)
        sheet.write(7, 4, 'Quantity', format66)
        sheet.write(7, 5, 'UOM', format66)

        # sheet.write(7, 5, 'Lot No', format66)
        # sheet.write(7, 6, 'Location', format66)
        # sheet.write(7, 7, 'Product Location', format66)
        # sheet.write(7, 8, 'Remark', format66)
        # sheet.write(7, 8, 'Status', format66)

        mrp_order = self.env['mrp.production'].search(
            [('date_planned_start', '>=', self.start_date),
             ('date_planned_finished', '<=', self.end_date)])

        row = 8

        number = 0
        for mrp in mrp_order:
            number += 1
            sheet.write(row, 0, number, row_format)
            sheet.write(row, 1, mrp.name, row_format)
            sheet.write(row, 2, mrp.date_planned_start, row_date_format)

            sheet.write(row, 3, mrp.product_id.name, row_format)
            sheet.write(row, 4, mrp.product_qty, qty_format)
            sheet.write(row, 5, mrp.product_uom_id.name, row_format)
            # sheet.write(row, 5, scrap.product_id.name, row_format)
            # sheet.write(row, 6, mrp.production_location_id.display_name, row_format)
            # sheet.write(row, 7, mrp.location_dest_id.display_name, row_format)
            # sheet.write(row, 8, tools.html2plaintext(scrap.notes), row_format)
            # sheet.write(row, 8, mrp.state, row_format)

            row += 1

        stream = BytesIO()
        workbook.save(stream)
        out = base64.encodebytes(stream.getvalue())
        exel_id = self.env['manufacturing.reports.exel'].create({'file_name': filename,
                                                                 'excel_file': out
                                                                 })
        return {
            'view_mode': 'form',
            'res_id': exel_id.id,
            'res_model': 'manufacturing.reports.exel',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


class SizeExcelReport(models.TransientModel):
    _name = "manufacturing.reports.exel"

    file_name = fields.Char(
        'Excel File',
        size=64,
        readonly=True,
    )

    excel_file = fields.Binary(
        'Download Report',
        readonly=True,
    )
