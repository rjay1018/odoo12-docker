# -*- coding: utf-8 -*-

from odoo import api, fields, models


class survey_answer_tag(models.Model):
    _name = "survey.answer.tag"

    name = fields.Char(
        string="Name",
        required=True,
    )
    