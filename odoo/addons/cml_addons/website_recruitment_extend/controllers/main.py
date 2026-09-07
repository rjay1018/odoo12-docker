# -*- coding: utf-8 -*-
# Part of Kiran Infosoft. See LICENSE file for full copyright and licensing details.

from datetime import datetime

from odoo import http, _
from odoo.http import request
from odoo.addons.website_hr_recruitment.controllers.main import WebsiteHrRecruitment
from odoo.addons.website_form.controllers.main import WebsiteForm


class WebsiteForm(WebsiteForm):

    @http.route('/website_form/<string:model_name>',
                type='http', auth="public",
                methods=['POST'], website=True)
    def website_form(self, model_name, **kwargs):
        if model_name == 'hr.applicant':
            for para in request.params:
                lang = request.env['ir.qweb.field'].user_lang()

                if para =='birthday':
                    birthday = request.params[para]
                    birthday = datetime.strptime(birthday, '%Y-%m-%d').strftime(lang.date_format)
                    request.params.update({'birthday': birthday})

                if para =='work_start_date':
                    work_start_date = request.params[para]
                    work_start_date = datetime.strptime(work_start_date, '%Y-%m-%d').strftime(lang.date_format)
                    request.params.update({'work_start_date': work_start_date})

                if para =='work_end_date':
                    work_end_date = request.params[para]
                    work_end_date = datetime.strptime(work_end_date, '%Y-%m-%d').strftime(lang.date_format)
                    request.params.update({'work_end_date': work_end_date})

            firstname = request.params.get('firstname', '')
            middlename = request.params.get('middlename', '')
            lastname = request.params.get('lastname', '')

            name_list = [lastname, middlename, firstname]
            name = ' '.join(name_list)
            request.params.update({'partner_name': name})

        return  super(WebsiteForm, self).website_form(model_name=model_name, kwargs=kwargs)


class WebsiteHrRecruitment(WebsiteHrRecruitment):

    @http.route('/jobs/apply/<model("hr.job"):job>', type='http', auth="public", website=True)
    def jobs_apply(self, job, **kwargs):
        error = {}
        default = {}
        if 'website_hr_recruitment_error' in request.session:
            error = request.session.pop('website_hr_recruitment_error')
            default = request.session.pop('website_hr_recruitment_default')
        sources = request.env['utm.source'].sudo().search([])
        countries = request.env['res.country'].sudo().search([])
        
        return request.render("website_recruitment_extend.apply_extend", {
            'job': job,
            'error': error,
            'default': default,
            'sources': sources,
            'countries': countries
        })
