# -*- coding: utf-8 -*-
import io
import xlwt
import base64
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _

class SurveyLable(models.Model):
    _inherit = "survey.label"

    answer_sequence_integer = fields.Integer(
        compute="_compute_answer_sequence_integer",
        string="Answer Sequence"
    )

    @api.depends('value')
    def _compute_answer_sequence_integer(self):
        for rec in self:
            answer_sequence_integer = 0
            num_val = 0
            num_val_list = rec.value.split('.')
            if num_val_list:
                num_val = num_val_list[0]
                try:
                    num_val = int(num_val)
                except:
                    num_val = 0
            rec.answer_sequence_integer = num_val


class Assessments(models.Model):
    _inherit = "survey.user_input"

    base_style = xlwt.easyxf(
        'font: name Times New Roman,bold on,height 400;align: horiz center;'
    )
    # Excel Styles
    style2_title = xlwt.easyxf(
        'font: name Times New Roman, bold on;align: horiz  left;',
        num_format_str='MM/DD/YYYY'
    )
    style2_title_center = xlwt.easyxf(
        'font: name Times New Roman, bold on;align: horiz  center;',
        num_format_str='MM/DD/YYYY'
    )
    style2_title_value = xlwt.easyxf(
        'font: name Times New Roman bold on;align: horiz  left;',
        num_format_str='MM/DD/YYYY'
    )
    style2_date = xlwt.easyxf(
        'font: name Times New Roman bold on;align: horiz  left;\
        borders: top thin, bottom thin, left thin, right thin;',
        num_format_str='MM/DD/YYYY HH:MM:SS'
    )
    table_data_right = xlwt.easyxf(
        'font: bold on;align: horiz  center;',
        num_format_str='#,##0'
    )
    table_data_right_border = xlwt.easyxf(
        'font:  bold on;align: horiz  center;\
        borders: top_color black, bottom_color black, right_color black, left_color black, \
        top thick, bottom thick, left thick, right thick;',
        num_format_str='#,##0'
    )

    table_title = xlwt.easyxf(
        'font: name Times New Roman, bold on;align: horiz  right;\
        pattern: pattern solid, fore_colour black;',
        num_format_str='#,##0.00'
    )

    def action_export_tsi_report(self):

        workbook = xlwt.Workbook()
        row_score_sheet = workbook.add_sheet('Row Score')
        scoring_sheet = workbook.add_sheet('Scoring Sheet')

        ans_by_sequence = {}
        for line in self.user_input_line_ids.sorted(
            key=lambda i : i.value_suggested_row.answer_sequence_integer
        ):
            ans_by_sequence[line.value_suggested_row.answer_sequence_integer] = line.quizz_mark


        row_score_list = [i for i in range(1, 101)]
        # Row Score Sheet
        row_count = 0
        line_count = 0
        for line in row_score_list:
            ansncell = 0
            value_cell = 1
            if line_count > 19 and line_count <= 39:
                ansncell = 2
                value_cell = 3
            elif line_count > 39 and line_count <= 59:
                ansncell = 4
                value_cell = 5
            elif line_count > 59 and line_count <= 79:
                ansncell = 6
                value_cell = 7
            elif line_count > 79 and line_count <= 99:
                ansncell = 8
                value_cell = 9
            elif line_count > 99:
                ansncell = 10
                value_cell = 11

            row_score_sheet.write(
                row_count,
                ansncell,
                '#' + str(line),
                self.table_data_right
            )
            row_score_sheet.write(
                row_count,
                value_cell,
                ans_by_sequence.get(line, 0),
                self.table_data_right_border
            )
            row_score_sheet.col(ansncell).width = 1500
            row_score_sheet.col(value_cell).width = 2000

            row_count += 1
            line_count += 1
            
            if row_count == 20:
                row_count = 0
            elif row_count == 40:
                row_count = 0
            elif row_count == 60:
                row_count = 0
            elif row_count == 80:
                row_count = 0
            elif row_count == 100:
                row_count = 0
            elif row_count == 120:
                row_count = 0

        # Scoring Sheet


#         ans_by_questions = {}
#         for line in self.user_input_line_ids.sorted(
#             key=lambda i : i.value_suggested_row.answer_sequence_integer
#         ):
#             if line.question_id not in ans_by_questions:
#                 ans_by_questions[line.question_id] = []
#             ans_by_questions[line.question_id].append(line)
# 
#         maks=max(ans_by_questions, key=lambda k: len(ans_by_questions[k]))
#         last_cell = (len(ans_by_questions[maks]) * 2) + 1

        row_atr_1 = [21, 43, 60, 65, 79, 82, 86, 92, 96, 99]
        row_rl_2 = [3, 5, 7, 11, 14, 27, 31, 49, 53, 56]
        row_aa_3 = [22, 27, 31, 41, 51, 54, 91, 97]
        row_d_4 = [7, 13, 17, 30, 64, 90, 98, 100]
        row_ai_5 = [3, 15, 34, 35, 37, 45, 57, 63, 93]
        row_ie_6 = [1, 8, 12, 62, 66, 70, 72, 74]
        row_da_7 = [2, 4, 23, 59, 67, 83, 87, 89]
        row_dis_8 = [10, 20, 26, 29, 38, 42, 84, 85, 88]
        row_sc_9 = [9, 33, 39, 47, 52, 61, 68, 77, 95]
        row_dsb_10 = [18, 28, 36, 46, 69, 71, 73, 76, 81]
        row_isr_11 = [6, 16, 24, 32, 44, 55, 75, 80, 94]
        row_trb_12 = [25, 35, 36, 45, 46, 48, 69, 78]

        last_cell = 22


        ans_by_questions = {
            'ATR': row_atr_1,
            'RL': row_rl_2,
            'AA': row_aa_3,
            'D':row_d_4,
            'AI': row_ai_5,
            'IE': row_ie_6,
            'DA':row_da_7,
            'DIS':row_dis_8,
            'SC':row_sc_9,
            'DSB':row_dsb_10,
            'ISR':row_isr_11,
            'TRB':row_trb_12
        }

        # First Scoring Table
        total_zero = 0
        row_count = 0
        total_table_score = 0
        total_lines_zero =0

        for q in ans_by_questions:
            scoring_sheet.write(
                row_count,
                0,
                q,
                self.table_data_right
            )
            ansncell = 1
            value_cell = 2
            total_ans_score = 0
            line_zero = 0
            for a in ans_by_questions[q]:
                quizz_mark = ans_by_sequence.get(a, 0)
                scoring_sheet.col(ansncell).width = 1500
                scoring_sheet.col(row_count).width = 1500
                scoring_sheet.col(value_cell).width = 1500
                scoring_sheet.write(
                    row_count,
                    ansncell,
                    '#' + str(a),
                    self.table_data_right
                )
                scoring_sheet.write(
                    row_count,
                    value_cell,
                    quizz_mark,
                    self.table_data_right_border
                )
                total_ans_score += quizz_mark

                if quizz_mark == 0:
                    total_zero += 1
                    line_zero += 1
                ansncell += 2
                value_cell += 2

            if q != 'RL':
                scoring_sheet.write(
                    row_count,
                    last_cell,
                    'SUM=',
                    self.table_data_right
                )
                scoring_sheet.write(
                    row_count,
                    last_cell+1,
                    total_ans_score,
                    self.table_data_right_border
                )
            else:
                scoring_sheet.write(
                    row_count,
                    last_cell,
                    r"0's=",
                    self.table_data_right
                )
                scoring_sheet.write(
                    row_count,
                    last_cell+1,
                    line_zero,
                    self.table_data_right_border
                )
                total_lines_zero = line_zero
            row_count += 1
            total_table_score += total_ans_score

        row_count += 1

        scoring_sheet.write(
            row_count,
            last_cell,
            'ROW SCORE',
            self.table_data_right
        )
        scoring_sheet.write(
            row_count,
            last_cell+1,
            total_table_score,
            self.table_data_right_border
        )

        row_count += 1

        scoring_sheet.write(
            row_count,
            0,
            'RL',
            self.table_data_right
        )
        scoring_sheet.write(
            row_count,
            1,
            total_lines_zero,
            self.table_data_right_border
        )
        scoring_sheet.write(
            row_count,
            2,
            '(No. of Zero answers)',
            self.table_data_right
        )

        row_count += 5

        # Second Table
        
        items_for_second_tables = [19,25,28,30,40,48,50,58,65,90,92,99]
        
        items_for_scores = self.user_input_line_ids.filtered(
            lambda o: o.value_suggested_row.answer_sequence_integer in items_for_second_tables).sorted(
            key=lambda i : i.value_suggested_row.answer_sequence_integer
        )

        for item in items_for_scores:
            scoring_sheet.write(
                row_count,
                0,
                '#' + str(item.value_suggested_row.answer_sequence_integer),
                self.table_data_right
            )
            scoring_sheet.write(
                row_count,
                1,
                item.quizz_mark,
                self.table_data_right_border
            )
            scoring_sheet.write(
                row_count,
                2,
                item.value_suggested_row.value,
                self.table_data_right
            )
            row_count+=1


        row_score_calc_list = [5,8,14,23,30,51,52,62,64,84,15,62,17,67,90,54,68,66,100,85]
        
        
        row_score_calcs = self.user_input_line_ids.filtered(
            lambda o: o.value_suggested_row.answer_sequence_integer in row_score_calc_list).sorted(
            key=lambda i : i.value_suggested_row.answer_sequence_integer
        )


        row_count += 5
        row_score_lists = [(5,15),(8, 62),(14, 17),(23, 67),(30, 90),(51, 54),(52, 68),(62, 66),(64, 100),(84, 85)]
        
        total_row_score = 0
        for r in row_score_lists:
            f_cell = self.user_input_line_ids.filtered(
                lambda o: o.value_suggested_row.answer_sequence_integer == r[0]
            )
            
            t_cell = self.user_input_line_ids.filtered(
                lambda o: o.value_suggested_row.answer_sequence_integer == r[1]
            )

            scoring_sheet.write(
                row_count,
                0,
                'AbVal',
                self.table_data_right
            )
            scoring_sheet.write(
                row_count,
                1,
                '#' + str(f_cell.value_suggested_row.answer_sequence_integer),
                self.table_data_right
            )
            scoring_sheet.write(
                row_count,
                2,
                f_cell.quizz_mark,
                self.table_data_right_border
            )
            scoring_sheet.write(
                row_count,
                3,
                '-',
                self.table_data_right
            )

            scoring_sheet.write(
                row_count,
                4,
                '#' + str(t_cell.value_suggested_row.answer_sequence_integer),
                self.table_data_right
            )
            scoring_sheet.write(
                row_count,
                5,
                t_cell.quizz_mark,
                self.table_data_right_border
            )

            scoring_sheet.write(
                row_count,
                6,
                '=',
                self.table_data_right
            )
            scoring_sheet.write(
                row_count,
                7,
                abs(f_cell.quizz_mark - t_cell.quizz_mark),
                self.table_data_right_border
            )

            total_row_score += abs((f_cell.quizz_mark - t_cell.quizz_mark))
            row_count+=1

        row_count += 1

        scoring_sheet.write(
            row_count,
            0,
            'AbVal',
            self.table_data_right
        )
        scoring_sheet.write(
            row_count,
            5,
            'INC RAW SCORE',
            self.table_data_right
        )
        scoring_sheet.write(
            row_count,
            6,
            '=',
            self.table_data_right
        )
        scoring_sheet.write(
            row_count,
            7,
            total_row_score,
            self.table_data_right_border
        )
        row_count += 1

        stream = io.BytesIO()

        workbook.save(stream)
        name = self.display_name + '.xls'
        attach_id = self.env['assesment.report.excel.output'].create({
            'name': name,
            'filename': base64.encodebytes(
                stream.getvalue()
            )
        })
        return {
            'type': 'ir.actions.act_window',
            'name': ('Report'),
            'res_model': 'assesment.report.excel.output',
            'res_id': attach_id.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

class AttendanceEXCEL(models.TransientModel):
    _name = 'assesment.report.excel.output'
    _description = 'Excel Report Output'

    name = fields.Char(
        string='File Name',
        size=256,
        readonly=True
    )
    filename = fields.Binary(
        string='File to Download',
        readonly=True
    )


