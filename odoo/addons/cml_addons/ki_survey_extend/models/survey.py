# -*- coding: utf-8 -*-
from odoo import api,fields,models


class Survey(models.Model):

    _inherit = 'survey.survey'

    user_confirmation = fields.Boolean(
        string="User Confirmation",
    )
    user_confirmation_content = fields.Html(
        string="User Confirmation Content"
    )


class survey_label(models.Model):

    _inherit = "survey.label"

    survey_tag_id = fields.Many2one(
        'survey.answer.tag',
        string="Survey Tag",
    )


class survey_user_input_line(models.Model):

    _inherit = "survey.user_input_line"

    survey_tag_id = fields.Many2one(
        'survey.answer.tag',
        string="Survey Tag",
        related="value_suggested_row.survey_tag_id",
    )
    answer_tag_id = fields.Many2one(
        'survey.answer.tag',
        string="Answer Tag",
        related="value_suggested.survey_tag_id",
    )
    question_name = fields.Char(
        string="Question Name",
        compute="_compute_question_name",
        store=True
    )
    answer_name = fields.Char(
        string="Answer Name",
        compute="_compute_answer_name",
        store=True
    )

    @api.depends('value_suggested_row', 'question_id')
    def _compute_question_name(self):
        for record in self:
            if record.value_suggested_row:
                record.question_name = str(record.value_suggested_row.display_name)
            else:
                record.question_name = str(record.question_id.question)

    @api.depends('value_date', 'value_free_text', 'value_number', 'value_suggested', 'value_suggested_row',
                 'value_text')
    def _compute_answer_name(self):
        for record in self:
            if record.value_date:
                record.answer_name = str(record.value_date)
            elif record.value_free_text:
                record.answer_name = str(record.value_free_text)
            elif record.value_number:
                record.answer_name = str(record.value_number)
            elif record.value_suggested:
                record.answer_name = str(record.value_suggested.display_name)
            elif record.value_suggested_row:
                record.answer_name = str(record.value_suggested_row.display_name)
            elif record.value_text:
                record.answer_name = str(record.value_text)
            else:
                record.answer_name =''

class survey_user_input(models.Model):

    _inherit = "survey.user_input"

    user_confirmation = fields.Boolean(
        string="User Confirmation",
        copy=False
    )
    relation_type = fields.Selection(
        [
            ('self', 'Self'),
            ('father', 'Parent'),
            ('teacher', 'Teacher'),
            ('guardian','Guardian')
        ],
        string="Relation Type",
        default='self',
        store=True
    )
    survey_category_id = fields.Many2one(
        'survey.user.category',
        'Survey Category',
        related="survey_id.survey_category_id",
        store=True
    )

    new_specialist_score = fields.Char(
        'Specialist Score'
    )
    new_quizz_score = fields.Char()

    @api.model
    def create(self, vals):
        try:
            if not vals.get('relation_type'):
                vals['relation_type'] = 'self'
        except:
            pass
        result = super(survey_user_input, self).create(vals)
        return result


class Survey(models.Model):
    _inherit = 'survey.survey'

    survey_category_id = fields.Many2one(
        'survey.user.category',
        'Survey Category'
    )
    mail_template_id = fields.Many2one(
        'mail.template',
        "Email Template",
        domain=[('model','=','survey.survey')]
    )
    notification_user_ids = fields.Many2many(
        'res.users',
        string="Users",
    )

    @api.multi
    def action_send_survey(self):
        call_super = super(Survey, self).action_send_survey()
        if self.mail_template_id:
            new_dict = call_super['context']
            new_dict.update({
                'default_use_template' : bool(self.mail_template_id),
                'default_template_id' : self.mail_template_id and self.mail_template_id.id or False,
            })
            call_super['context'] = new_dict
        return call_super
