from odoo import fields, models, api
import time
from io import BytesIO
from collections import OrderedDict
import pytz
import xlsxwriter
import base64
from datetime import datetime, date
from pytz import timezone

class MsGenericExcelReportWizard(models.TransientModel):
    _name = "ms.generic.excel.report.wizard"
    _description = "Generic Excel Report Wizard"
    _rec_name = "report_id"

    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone('Asia/Jakarta'))

    data = fields.Binary('File', readonly=True)
    name = fields.Char('Filename', readonly=True)
    report_id = fields.Many2one('ms.generic.excel.report', string='Report', ondelete='cascade')
    code = fields.Char(string='Code', related='report_id.code')

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self._context.get('report_id'):
            res['report_id'] = self._context['report_id']
        return res

    def cell_format(self, workbook):
        cell_format = {}
        cell_format['title'] = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 20,
            'font_name': self.report_id.font_name,
        })
        cell_format['no'] = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
        })
        cell_format['header'] = workbook.add_format({
            'bold': True,
            'align': 'center',
            'bg_color': self.report_id.background_color,
            'border': True,
            'font_name': self.report_id.font_name,
        })
        cell_format['content'] = workbook.add_format({
            'font_size': 11,
            'border': True,
            'font_name': self.report_id.font_name,
        })
        cell_format['content_float'] = workbook.add_format({
            'font_size': 11,
            'border': True,
            'num_format': '#,##0.00',
            'font_name': self.report_id.font_name,
        })
        cell_format['total'] = workbook.add_format({
            'bold': True,
            'bg_color': self.report_id.background_color,
            'num_format': '#,##0.00',
            'border': True,
            'font_name': self.report_id.font_name,
        })
        return cell_format, workbook

    def action_print(self):
        self.ensure_one()
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        cell_format, workbook = self.cell_format(workbook)
        worksheet = workbook.add_worksheet(self.report_id.name)
        column_length = self.report_id.report_line and len(self.report_id.report_line) or 0
        if not column_length :
            return False
        column_length
        no = 1
        column = 1

        worksheet.set_column('A:A', 6)
        worksheet.set_column(1, column_length, 30)
        worksheet.merge_range(0, 0, 1, column_length, self.report_id.name, cell_format['title'])
        worksheet.write('A4', 'NO', cell_format['header'])
        
        for col in self.report_id.report_line :
            worksheet.write(3, column, col.name, cell_format['header'])
            column += 1
        data_list = self.report_id.with_context(wizard_id=self).get_data()
        data_list = self.finalize_data(data_list)
        row = 5
        column_float_number = {}
        for data in data_list :
            worksheet.write('A%s'%row, no, cell_format['no'])
            no += 1
            column = 1
            for value in data :
                if type(value) is int or type(value) is float :
                    content_format = 'content_float'
                    column_float_number[column] = column_float_number.get(column, 0) + value
                else :
                    content_format = 'content'
                if isinstance(value, datetime):
                    value = pytz.UTC.localize(value).astimezone(timezone(self.env.user.tz or 'UTC'))
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(value, date):
                    value = value.strftime('%Y-%m-%d')
                worksheet.write(row-1, column, value, cell_format[content_format])
                column += 1
            row += 1

        row -= 1
        for x in range(column_length+1):
            if x == 0 :
                worksheet.write('A%s'%(row+1), 'Total', cell_format['header'])
            elif x not in column_float_number :
                worksheet.write(row, x, '', cell_format['header'])
            else :
                worksheet.write(row, x, column_float_number[x], cell_format['total'])

        workbook.close()
        result = base64.encodestring(fp.getvalue())
        date_string = self.get_default_date_model().strftime("%Y-%m-%d")
        filename = '%s %s'%(self.report_id.name, date_string)
        filename += '%2Exlsx'
        self.write({'data':result})
        url = "web/content/?model="+self._name+"&id="+str(self.id)+"&field=data&download=true&filename="+filename
        return {
            'name': 'Generic Excel Report',
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def finalize_data(self, data_list):
        return data_list
