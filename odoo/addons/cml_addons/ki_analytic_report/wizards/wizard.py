from odoo import models, fields, api
import xlwt
import base64
from io import BytesIO
from datetime import date, datetime, timedelta


class AnalyticReport(models.TransientModel):
    _name = "analytic.period.report.wizard"
    _description = "Analytic Report "

    analytic_account_ids = fields.Many2many(
        'account.analytic.account',
        string="Analytic Account",
        required=False,
    )
    analytic_tag_ids = fields.Many2many(
        'account.analytic.tag',
        string="Analytic Tag",
        required=False,
    )
    start_date = fields.Date(
        string="Start Date",
        required=True
    )
    end_date = fields.Date(
        string="End Date",
        required=True
    )

    filter_group = fields.Selection([
        ('analytic_account', 'Analytic Account'),
        ('analytic_tag', 'Analytic Tag'),
    ],
        required=True,
        default='analytic_account',
        string='Filter And Group By'
    )

    def export_xls(self):
        filename = "Analytic Report.xls"
        workbook = xlwt.Workbook(encoding='utf-8')
        sheet = workbook.add_sheet('sheet1')
        format1 = xlwt.easyxf("align:horiz center;font:color black,bold True;font: height 250,bold 0, color black;borders: top_color black, bottom_color black, right_color black, left_color black,\
                        left thin, right thin, top thin, bottom thin;")
        format0 = xlwt.easyxf("align:horiz right;font:color black,bold True;font: height 250,bold 0, color black;borders: top_color black, bottom_color black, right_color black, left_color black,\
                        left thin, right thin, top thin, bottom thin;")
        sheet.col(0).width = 7000
        sheet.col(1).width = 7000
        sheet.col(2).width = 7000
        sheet.col(3).width = 7000
        sheet.col(4).width = 7000
        sheet.col(5).width = 7000
        sheet.col(7).width = 7000
        sheet.col(8).width = 9000
        format22 = xlwt.easyxf("align: horiz center;font: height 350,bold 1, color black;pattern: pattern solid, fore_colour light_green;borders: top_color black, bottom_color black, right_color black, left_color black,\
                        left thin, right thin, top thin, bottom thin;", num_format_str='DD/MM/YYYY')
        format2 = xlwt.easyxf("align: horiz center;font: height 350,bold 1, color black;pattern: pattern solid, fore_colour light_green;borders: top_color black, bottom_color black, right_color black, left_color black,\
                        left thin, right thin, top thin, bottom thin;")

        format3 = xlwt.easyxf("align: horiz center;font: height 250,bold 1, color black;pattern: pattern solid, fore_colour green;borders: top_color black, bottom_color black, right_color black, left_color black,\
                        left thin, right thin, top thin, bottom thin;")

        format4 = xlwt.easyxf("align: horiz center;font: height 250,bold 1, color black;pattern: pattern solid, fore_colour light_green;borders: top_color black, bottom_color black, right_color black, left_color black,\
                        left thin, right thin, top thin, bottom thin;")
        format44 = xlwt.easyxf("align: horiz right;font: height 250,bold 1, color black;pattern: pattern solid, fore_colour light_green;borders: top_color black, bottom_color black, right_color black, left_color black,\
                        left thin, right thin, top thin, bottom thin;")

        sheet.write(2, 0, ' ', format3)
        header_col = 0
        rows = 0
        if self.filter_group == 'analytic_account':

            analytic_account_ids = self.analytic_account_ids
            if not analytic_account_ids:
                analytic_account_ids = self.env['account.analytic.account'].search([])

            date1 = self.start_date
            date2 = self.end_date
            date1 = date1.replace(day=1)
            date2 = date2.replace(day=1)
            data_dicts = {}
            total_dic = {}
            months = []
            while date1 <= date2:
                month = date1.month
                year = date1.year
                next_month = month + 1 if month != 12 else 1
                next_year = year + 1 if next_month == 1 else year
                date_list = [date1]

                date1 = date1.replace(month=next_month, year=next_year)
                end_date = date1 - timedelta(days=1)
                date_list.append(end_date)
                months.append(date_list)

            for line in months:
                start_date = line[0]
                end_date = line[1]
                account_groups = self.env['account.analytic.line'].search(
                    [('account_id', 'in', analytic_account_ids.ids),
                     ('date', '>=', start_date),
                     ('date', '<=', end_date)])
                for res in account_groups:
                    month_name = res.date.strftime("%B")
                    if month_name not in data_dicts:
                        data_dicts[month_name] = {}
                    if res.account_id not in data_dicts[month_name]:
                        data_dicts[month_name][res.account_id] = {
                            'month_wise_amount': 0
                        }
                    data_dicts[month_name][res.account_id]['month_wise_amount'] += res.amount
                    if res.account_id not in total_dic:
                        total_dic[res.account_id] = {
                            'acc_wise_total': 0
                        }
                    total_dic[res.account_id]['acc_wise_total'] += res.amount
            count = 2
            col = 1
            cols = 0

            row_col = 3
            analytic_account_row_dict = {}

            for rec in analytic_account_ids:
                sheet.row(row_col).height = 350
                sheet.write(row_col, cols, rec.name, format1)
                analytic_account_row_dict[rec] = row_col
                row_col += 1

            sheet.write(row_col, cols, 'Totals', format4)
            row_sums = 0
            for month_name in data_dicts:

                sheet.row(count).height = 350
                sheet.write(count, col, month_name, format3)
                row_sum = 0

                for analytic_account in data_dicts[month_name]:
                    row_sum += data_dicts[month_name][analytic_account]['month_wise_amount']
                    row_sums += data_dicts[month_name][analytic_account]['month_wise_amount']
                    sheet.write(analytic_account_row_dict[analytic_account], col,
                                data_dicts[month_name][analytic_account]['month_wise_amount'], format0)
                col += 1
                cols += 1
                sheet.write(row_col, cols, row_sum, format44)
            cols += 1
            sheet.row(row_col).height = 350
            sheet.write(row_col, cols, row_sums, format44)
            sheet.row(count).height = 350
            sheet.write(count, col, 'Total', format3)
            header_col = col
            for rec in analytic_account_ids:
                if rec in total_dic:
                    sheet.write(analytic_account_row_dict[rec], col, total_dic[rec]['acc_wise_total'], format44)
                else:
                    sheet.write(analytic_account_row_dict[rec], col, ' ', format44)
            col += 1

 # --------------------------------------------------------------------------------------------------------------------

        if self.filter_group == 'analytic_tag':
            analytic_tag_ids = self.analytic_tag_ids
            if not analytic_tag_ids:
                analytic_tag_ids = self.env['account.analytic.tag'].search([])

            date1 = self.start_date
            date2 = self.end_date
            date1 = date1.replace(day=1)
            date2 = date2.replace(day=1)
            data_dicts = {}
            total_dic = {}
            months = []
            while date1 <= date2:
                month = date1.month
                year = date1.year
                next_month = month + 1 if month != 12 else 1
                next_year = year + 1 if next_month == 1 else year
                date_list = [date1]

                date1 = date1.replace(month=next_month, year=next_year)
                end_date = date1 - timedelta(days=1)
                date_list.append(end_date)
                months.append(date_list)

            for line in months:
                start_date = line[0]
                end_date = line[1]
                account_groups = self.env['account.analytic.line'].search(
                    [('tag_ids', 'in', analytic_tag_ids.ids),
                     ('date', '>=', start_date),
                     ('date', '<=', end_date)])
                for res in account_groups:
                    month_name = res.date.strftime("%B")
                    if month_name not in data_dicts:
                        data_dicts[month_name] = {}
                    if res.tag_ids not in data_dicts[month_name]:
                        data_dicts[month_name][res.tag_ids] = {
                            'month_wise_amount': 0
                        }
                    data_dicts[month_name][res.tag_ids]['month_wise_amount'] += res.amount
                    if res.tag_ids not in total_dic:
                        total_dic[res.tag_ids] = {
                            'acc_wise_total': 0
                        }
                    total_dic[res.tag_ids]['acc_wise_total'] += res.amount
            count = 2
            col = 1
            cols = 0
            rows = 0

            row_col = 3
            analytic_account_row_dict = {}

            for rec in analytic_tag_ids:
                sheet.row(row_col).height = 350
                sheet.write(row_col, cols, rec.name, format1)
                analytic_account_row_dict[rec] = row_col
                row_col += 1

            sheet.write(row_col, cols, 'Total', format4)
            row_sums = 0
            for month_name in data_dicts:
                sheet.row(rows).height = 750
                sheet.row(count).height = 350
                sheet.write(count, col, month_name, format3)
                row_sum = 0
                for analytic_account in data_dicts[month_name]:
                    row_sum += data_dicts[month_name][analytic_account]['month_wise_amount']
                    row_sums += data_dicts[month_name][analytic_account]['month_wise_amount']
                    sheet.write(analytic_account_row_dict[analytic_account], col,
                                data_dicts[month_name][analytic_account]['month_wise_amount'], format0)
                col += 1
                cols += 1
                sheet.write(row_col, cols, row_sum, format44)
            cols += 1
            sheet.row(row_col).height = 350
            sheet.write(row_col, cols, row_sums, format44)
            sheet.row(count).height = 350
            sheet.write(count, col, 'Total', format3)
            header_col = col
            for rec in analytic_tag_ids:
                if rec in total_dic:
                    sheet.write(analytic_account_row_dict[rec], col, total_dic[rec]['acc_wise_total'], format44)
                else:
                    sheet.write(analytic_account_row_dict[rec], col, ' ', format44)
            col += 1
        sheet.row(rows).height = 750

        start_date = self.start_date.strftime('%d/%m/%Y')
        end_date = self.end_date.strftime('%d/%m/%Y')

        date = 'MONTHLY EXPENSES: {} To {} '.format(start_date, end_date)

        sheet.write_merge(rows, 0, rows, header_col, date, format22)

        stream = BytesIO()
        workbook.save(stream)
        out = base64.encodebytes(stream.getvalue())
        exel_id = self.env['analytic.reports.exel'].create({'file_name': filename,
                                                            'excel_file': out
                                                            })
        return {
            'view_mode': 'form',
            'res_id': exel_id.id,
            'res_model': 'analytic.reports.exel',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


class SizeExcelReport(models.TransientModel):
    _name = "analytic.reports.exel"

    file_name = fields.Char(
        'Excel File',
        size=64,
        readonly=True,
    )

    excel_file = fields.Binary(
        'Download Report',
        readonly=True,
    )
