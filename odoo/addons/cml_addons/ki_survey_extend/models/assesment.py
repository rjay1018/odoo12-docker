# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PageWiseAssesment(models.Model):
    _inherit = "assesment.pagewise.summary"

    survey_tag_id = fields.Many2one(
        'survey.answer.tag',
        string="Survey Tag",
    )
    survey_tag_input_id = fields.Many2one(
        'survey.user_input',
        string="Survey Input"
    )


class SurveyInput(models.Model):
    _inherit = "survey.user_input"


    tagwise_summary_ids = fields.One2many(
        'assesment.pagewise.summary',
        'survey_tag_input_id',
        string="Tag Wise Summary",
        readonly=True
    )

    @api.multi
    def write(self, vals):
        res = super(SurveyInput, self).write(vals)
        if vals.get('state', '') == 'done':
            self.action_compute_score_summary()
        return res

    def action_compute_score_summary(self):
        super(SurveyInput, self).action_compute_score_summary()
        for rec in self:
            rec.tagwise_summary_ids = [(6, 0, [])]
            page_ids = rec.user_input_line_ids.mapped('survey_tag_id')
            lines = []
            for page in page_ids:
                answers = rec.user_input_line_ids.filtered(lambda p: p.survey_tag_id == page)
                total_score = sum(a.quizz_mark for a in answers)
                average = total_score / len(answers)
                line_vals = {
                    'survey_tag_id': page.id,
                    'total_score': total_score,
                    'average_score': average
                }
                lines.append((0, 0, line_vals))
            rec.tagwise_summary_ids = lines
