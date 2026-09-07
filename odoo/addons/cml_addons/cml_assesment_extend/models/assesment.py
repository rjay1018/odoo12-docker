# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PageWiseAssesment(models.Model):
    _name = "assesment.pagewise.summary"

    page_id = fields.Many2one(
        'survey.page',
        string="Page"
    )
    total_score = fields.Float(
        string="Total Score"
    )
    average_score = fields.Float(
        string="Average Score"
    )
    survey_input_id = fields.Many2one(
        'survey.user_input',
        string="Survey Input"
    )


class SurveyInput(models.Model):
    _inherit = "survey.user_input"

    @api.depends(
        'user_input_line_ids',
        'user_input_line_ids.quizz_mark'
    )
    def _compute_scores(self):
        for rec in self:
            answers = rec.user_input_line_ids
            total_score = average = 0.0
            if answers:
                total_score = sum(a.quizz_mark for a in answers)
                average = total_score / len(answers)
            rec.total_score = total_score
            rec.average_score = average
            

    pagewise_summary_ids = fields.One2many(
        'assesment.pagewise.summary',
        'survey_input_id',
        string="Page Wise Summary",
        readonly=True
    )

    total_score = fields.Float(
        string="Total Score",
        compute='_compute_scores',
        store=True
    )
    average_score = fields.Float(
        string="Average Score",
        compute='_compute_scores',
        store=True
    )


    def action_compute_score_summary(self):
        for rec in self:
            rec.pagewise_summary_ids = [(6, 0, [])]
            page_ids = rec.user_input_line_ids.mapped('page_id')
            lines = []
            for page in page_ids:
                answers = rec.user_input_line_ids.filtered(lambda p: p.page_id == page)
                total_score = sum(a.quizz_mark for a in answers)
                average = total_score / len(answers)
                line_vals = {
                    'page_id': page.id,
                    'total_score': total_score,
                    'average_score': average
                }
                lines.append((0, 0, line_vals))
            rec.pagewise_summary_ids = lines
