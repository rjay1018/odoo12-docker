from odoo import models, fields, api, _
import xlwt
import base64
import io
from io import BytesIO


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def formatINR(self, number):

        number = "{:.2f}".format(number)
        s, *d = str(number).partition(".")
        r = ",".join([s[x - 2:x] for x in range(-3, -len(s), -2)][::-1] + [s[-3:]])
        amt = "".join([r] + d)
        return amt

    def action_download_excel(self):
        # number = 15202112.25655
        # self.formatINR(number)
        filename = "Payroll Report.xls"
        # output = io.BytesIO()
        # workbook = xlwt.Workbook(output, {'in_memory': True})
        workbook = xlwt.Workbook(encoding='utf-8')
        sheet1 = workbook.add_sheet("Payroll Report", cell_overwrite_ok=True)
        style1 = xlwt.easyxf("align:horiz center;align:vertical center;font:color black,bold True;")
        format66 = xlwt.easyxf("align: horiz center;")

        float_value_right = xlwt.easyxf("align: horiz right;")

        table_title = xlwt.easyxf(
            'font: name Times New Roman;align: horiz  right;\
            borders: top_color black, bottom_color black, right_color black, left_color black, \
            top thin, bottom thin, left thin, right thin;',
            num_format_str='#,##0'
        )

        ADJUSTMENT_TYPE = {
            'adjustment': 'Adjustment',
            'allowance': 'Allowance',
            'cashadvance': 'Cash Advance',
            'loan': 'Loan',
            'otherbenefit': 'Other Benefit',
            'otherearning': 'Other Earning',
            'otherdeduct': 'Other Deduction',
            'refund': 'Refund',
            '13th_mo': '13th Month Pay',
            '14th_mo': '14th Month Pay'
        }
        earn_list = ['allowance', 'otherbenefit', 'otherearning', 'refund', '13th_mo', '14th_mo']
        deduct_list = ['cashadvance', 'loan', 'otherdeduct']
        company_id = self.env.user.company_id
        sheet1.write_merge(0, 1, 0, 4, company_id.name, style1)
        sheet1.write(2, 0, company_id.street, style1)
        sheet1.write(2, 1, company_id.street2, style1)
        sheet1.write(2, 2, company_id.city, style1)
        sheet1.write(2, 3, company_id.state_id.name, style1)
        sheet1.write(2, 4, company_id.zip, style1)
        sheet1.write(2, 5, company_id.country_id.name, style1)

        sheet1.write_merge(5, 5, 2, 4, 'WAGE INFO', style1)
        sheet1.write_merge(5, 5, 5, 26, 'OVERVIEW', style1)
        sheet1.write_merge(5, 5, 28, 35, 'PREMIUMS/BENEFITS', style1)
        sheet1.write_merge(5, 5, 39, 42, 'UNPAID LEAVE/ABSENT', style1)
        sheet1.write(6, 0, '#', format66)
        sheet1.write(6, 1, 'Employee')
        sheet1.write(6, 2, 'Wage Type')
        sheet1.write(6, 3, 'Basic Wage')
        sheet1.write(6, 4, 'Daily Pay')
        sheet1.write(6, 5, 'Reg. Worked Days')
        sheet1.write(6, 6, 'Paid. Reg. Hol.')
        sheet1.write(6, 7, 'Paid Leave')
        sheet1.write(6, 8, 'Unpaid Leave/Absent')
        sheet1.write(6, 9, 'Late')
        sheet1.write(6, 10, 'Undertime')
        sheet1.write(6, 11, 'Overtime')
        sheet1.write(6, 12, 'Night Diff.')
        sheet1.write(6, 13, 'BASIC PAY.')
        sheet1.write(6, 14, 'Paid. Reg. Hol. Amt.')
        sheet1.write(6, 15, 'COLA')
        sheet1.write(6, 16, 'Unpaid Leave/Absent Amt.')
        sheet1.write(6, 17, 'Late Amt.')
        sheet1.write(6, 18, 'Undertime Amt.')
        sheet1.write(6, 19, 'Overtime Amt.')
        sheet1.write(6, 20, 'Night Diff. Amt.')
        sheet1.write(6, 21, 'Total Premium (EE)')
        sheet1.write(6, 22, 'GROSS TAXABLE')
        sheet1.write(6, 23, 'W-Tax')
        sheet1.write(6, 24, 'Other Earn. (Non-Tax)')
        sheet1.write(6, 25, 'Other Deduction')
        sheet1.write(6, 26, 'NET PAY')
        sheet1.write(6, 27, '')
        sheet1.write(6, 28, 'HDMF (EE)')
        sheet1.write(6, 29, 'HDMF (ER)')
        sheet1.write(6, 30, 'PHIC (EE)')
        sheet1.write(6, 31, 'PHIC (ER)')
        sheet1.write(6, 32, 'SSS (EE)')
        sheet1.write(6, 33, 'SSS MPF (EE)')
        sheet1.write(6, 34, 'SSS (ER)')
        sheet1.write(6, 35, 'SSS MPF (ER)')
        sheet1.write(6, 36, '')
        sheet1.write(6, 37, '13th Month Pay')
        sheet1.write(6, 38, '')
        sheet1.write(6, 39, 'Half Day')
        sheet1.write(6, 40, 'Half Day Amt.')
        sheet1.write(6, 41, 'Absent')
        sheet1.write(6, 42, 'Absent Amt.')

        payslip = self.env['hr.payslip.run'].sudo().search([])
        index = 1
        col = 7
        deduction_list = []
        earning_list = []
        employee_row = {}
        earn_deduction_dct = {}
        for rec in self:
            for data in rec.slip_ids:
                if data.employee_id not in earn_deduction_dct:
                    earn_deduction_dct[data.employee_id] = {}

                for sum in data.slip_structure_ids:
                    for earn in earn_list:
                        if ADJUSTMENT_TYPE[earn] not in earn_deduction_dct[data.employee_id]:
                            earn_deduction_dct[data.employee_id][ADJUSTMENT_TYPE[earn]] = 0
                        if ADJUSTMENT_TYPE[earn] not in earning_list:
                            earning_list.append(ADJUSTMENT_TYPE[earn])
                    for deduc in deduct_list:
                        if ADJUSTMENT_TYPE[deduc] not in earn_deduction_dct[data.employee_id]:
                            earn_deduction_dct[data.employee_id][ADJUSTMENT_TYPE[deduc]] = 0
                        if ADJUSTMENT_TYPE[deduc] not in deduction_list:
                            deduction_list.append(ADJUSTMENT_TYPE[deduc])

                    if sum.adjustment_type in earn_list:
                        if ADJUSTMENT_TYPE[sum.adjustment_type] not in earn_deduction_dct[data.employee_id]:
                            earn_deduction_dct[data.employee_id][ADJUSTMENT_TYPE[sum.adjustment_type]] = 0
                        earn_deduction_dct[data.employee_id][ADJUSTMENT_TYPE[sum.adjustment_type]] += sum.amount
                        if ADJUSTMENT_TYPE[sum.adjustment_type] not in earning_list:
                            earning_list.append(ADJUSTMENT_TYPE[sum.adjustment_type])

                    if sum.adjustment_type in deduct_list:
                        if ADJUSTMENT_TYPE[sum.adjustment_type] not in earn_deduction_dct[data.employee_id]:
                            earn_deduction_dct[data.employee_id][ADJUSTMENT_TYPE[sum.adjustment_type]] = 0
                        earn_deduction_dct[data.employee_id][ADJUSTMENT_TYPE[sum.adjustment_type]] += sum.amount
                        if ADJUSTMENT_TYPE[sum.adjustment_type] not in deduction_list:
                            deduction_list.append(ADJUSTMENT_TYPE[sum.adjustment_type])

                sheet1.write(col, 0, index, format66)
                sheet1.write(col, 1, data.employee_id.name)
                employee_row[data.employee_id] = col
                sheet1.write(col, 2, data.wage_type)
                sheet1.write(col, 3, self.formatINR(data.wage), float_value_right)
                sheet1.write(col, 4, self.formatINR(data.daily_pay), float_value_right)
                sheet1.write(col, 5, data.work_days, float_value_right)
                sheet1.write(col, 6, data.regular_holiday, float_value_right)
                sheet1.write(col, 7, data.paid_leave, float_value_right)
                sheet1.write(col, 8, data.unpaid_leave, float_value_right)
                sheet1.write(col, 9, data.late, float_value_right)
                sheet1.write(col, 10, data.undertime, float_value_right)
                sheet1.write(col, 11, data.overtime, float_value_right)
                sheet1.write(col, 12, data.night_diff, float_value_right)
                sheet1.write(col, 13, self.formatINR(data.basic_pay), float_value_right)
                sheet1.write(col, 14, self.formatINR(data.regular_holiday_amount), float_value_right)
                sheet1.write(col, 15, self.formatINR(data.cola_amount), float_value_right)
                sheet1.write(col, 16, self.formatINR(data.unpaid_leave_amount), float_value_right)
                sheet1.write(col, 17, self.formatINR(data.late_amount), float_value_right)
                sheet1.write(col, 18, self.formatINR(data.undertime_amount), float_value_right)
                sheet1.write(col, 19, self.formatINR(data.overtime_amount), float_value_right)
                sheet1.write(col, 20, self.formatINR(data.night_diff_amount), float_value_right)
                sheet1.write(col, 21, self.formatINR(data.total_premium), float_value_right)
                sheet1.write(col, 22, self.formatINR(data.gross_pay), float_value_right)
                sheet1.write(col, 23, self.formatINR(data.wtax), float_value_right)
                sheet1.write(col, 24, self.formatINR(data.other_earning), float_value_right)
                sheet1.write(col, 25, self.formatINR(data.other_deduction), float_value_right)
                sheet1.write(col, 26, self.formatINR(data.net_pay), float_value_right)
                sheet1.write(col, 27, '')
                sheet1.write(col, 28, self.formatINR(data.hdmf_ee), float_value_right)
                sheet1.write(col, 29, self.formatINR(data.hdmf_er), float_value_right)
                sheet1.write(col, 30, self.formatINR(data.phic_ee), float_value_right)
                sheet1.write(col, 31, self.formatINR(data.phic_er), float_value_right)
                sheet1.write(col, 32, self.formatINR(data.sss_ee), float_value_right)
                sheet1.write(col, 33, self.formatINR(data.sss_ee_mpf), float_value_right)
                sheet1.write(col, 34, self.formatINR(data.sss_er), float_value_right)
                sheet1.write(col, 35, self.formatINR(data.sss_er_mpf), float_value_right)
                sheet1.write(col, 36, '')
                sheet1.write(col, 37, self.formatINR(data.month_13th), float_value_right)
                sheet1.write(col, 38, '')
                sheet1.write(col, 39, data.halfday, float_value_right)
                sheet1.write(col, 40, self.formatINR(data.halfday_amount), float_value_right)
                sheet1.write(col, 41, data.absent, float_value_right)
                sheet1.write(col, 42, self.formatINR(data.absent_amount), float_value_right)
                index += 1
                col += 1
        final_data = {}
        ded_row_count = 44
        for deduction in deduction_list:
            sheet1.write(6, ded_row_count, deduction)
            final_data[deduction] = ded_row_count
            ded_row_count += 1
        ear_row = ded_row_count + 1
        ear_row_count = ded_row_count + 1
        for earn in earning_list:
            sheet1.write(6, ear_row_count, earn)
            final_data[earn] = ear_row_count
            ear_row_count += 1

        earning_index = final_data[earning_list[-1]]
        deduct_index = final_data[deduction_list[-1]]
        sheet1.write_merge(5, 5, ear_row, earning_index, 'Earnings', style1)
        sheet1.write_merge(5, 5, 44, deduct_index, 'Deduction', style1)
        for ear_deduction_data in earn_deduction_dct:

            if earn_deduction_dct[ear_deduction_data] == {}:
                earn_deduct_row = employee_row[ear_deduction_data]
                for vals in earn_deduction_dct[ear_deduction_data]:
                    earn_deduct_col = final_data[vals]
                    sheet1.write(earn_deduct_row, earn_deduct_col, 0)
            else:
                earn_deduct_row = employee_row[ear_deduction_data]
                for vals in earn_deduction_dct[ear_deduction_data]:
                    earn_deduct_col = final_data[vals]
                    sheet1.write(earn_deduct_row, earn_deduct_col,
                                 self.formatINR(earn_deduction_dct[ear_deduction_data][vals]), float_value_right)

        stream = BytesIO()
        workbook.save(stream)
        out = base64.encodebytes(stream.getvalue())
        exel_id = self.env['payroll.reports.exel'].create({'file_name': filename,
                                                           'excel_file': out
                                                           })
        return {
            'view_mode': 'form',
            'res_id': exel_id.id,
            'res_model': 'payroll.reports.exel',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

        # output.seek(0)
        #
        # stream = BytesIO()
        # workbook.save(stream)
        # encoded_excel_file = base64.encodebytes(stream.getvalue())
        #
        #
        # attachment = self.env['ir.attachment'].create({
        #     'name':filename,
        #     'datas': encoded_excel_file,
        #     'datas_fname': filename,
        #     'res_model': 'hr.payslip.run',
        #     'type': 'binary',
        # })
        #
        # download_url = '/web/content/%s?download=true' % attachment.id
        # return {
        #     'type': 'ir.actions.act_url',
        #     'url': download_url,
        #     'target': 'self',
        # }


class SizeExcelReport(models.TransientModel):
    _name = "payroll.reports.exel"

    file_name = fields.Char(
        'Excel File',
        size=64,
        readonly=True,
    )

    excel_file = fields.Binary(
        'Download Report',
        readonly=True,
    )
