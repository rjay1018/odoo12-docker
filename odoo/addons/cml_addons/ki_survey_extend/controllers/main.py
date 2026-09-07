# -*- coding: utf-8 -*-

from odoo import fields, http
from odoo.http import request
from odoo.addons.survey.controllers.main import Survey


class SurveyInherit(Survey):

    @http.route(['/survey/fill/<model("survey.survey"):survey>/<string:token>',
                 '/survey/fill/<model("survey.survey"):survey>/<string:token>/<string:prev>'],
                type='http', auth='public', website=True)
    def fill_survey(self, survey, token, prev=None, **post):
        res = super(SurveyInherit, self).fill_survey(survey, token, prev, **post)
        UserInput = request.env['survey.user_input']
        user_input = UserInput.sudo().search([('token', '=', token)], limit=1)
        UserInputLine = request.env['survey.user_input_line']
        previous_answers = UserInputLine.sudo().search([('user_input_id.token', '=', token)])
        partner_val = {}

        for ans in previous_answers:
            if ans.question_id and ans.question_id.link_partner:

                if ans.question_id.partner_field_name == 'name':
                    partner_val.update({"name": ans.value_text})
                elif ans.question_id.partner_field_name == 'email':
                    partner_val.update({"email": ans.value_text})
                elif ans.question_id.partner_field_name == 'mobile':
                    partner_val.update({"mobile": ans.value_text})
                elif ans.question_id.partner_field_name == 'birthday':
                    partner_val.update({"birthday": ans.value_text})

                partner_val.update({
                    'is_respondent': True,
                    'is_client': False
                })

        search_domain = []
        if partner_val.get('name', False):
            search_domain.append(('name', 'ilike', partner_val['name']))
        if partner_val.get('birthday', False):
            search_domain.append(('birthday', '=', partner_val['birthday']))
        if partner_val.get('email', False):
            search_domain.append(('email', '=', partner_val['email']))

        partner_id = False
        if partner_val:
            partner_id = request.env['res.partner'].sudo().search(search_domain,limit=1)
            if not partner_id:
                partner_id = request.env['res.partner'].sudo().create(partner_val)
            else:
                partner_id.update(partner_val)
        if user_input.state == 'done':
            res_model_id = request.env['ir.model'].sudo().search([('model', '=', 'survey.survey')])
            for user in survey.sudo().notification_user_ids:
                mail = request.env['mail.activity'].sudo().create({
                    'activity_type_id': request.env.ref('ki_survey_extend.mail_activity_type_survey_submission').id,
                    'res_id': survey.id,
                    'date_deadline': fields.Date.today(),
                    'res_model_id': res_model_id.id,
                    'user_id': user.id
                })
        if user_input:
            if not user_input.user_confirmation:
                if survey.user_confirmation:
                    user_input.write({'user_confirmation': True})
            if partner_id:
                user_input.write({'partner_id': partner_id.id})

        return res
