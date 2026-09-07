# -*- coding: utf-8 -*-

from odoo import http,_
from odoo.http import request,route
from collections import OrderedDict
from odoo.addons.portal.controllers.portal import CustomerPortal, pager
from datetime import datetime
import base64


class CustomerPortal(CustomerPortal):

    @http.route(['/contact/update/<int:partner_id>/<int:contact_line_id>'], type='http', auth='user', website=True)
    def emergency_contact_update(self, partner_id, contact_line_id, **kw):
        print(kw)
        res_partner_id = request.env['res.partner'].sudo().search([('id', '=', partner_id)])
        if res_partner_id and contact_line_id and contact_line_id in res_partner_id.emergency_line_ids.ids:
            request.env['emergency.lines'].sudo().search(
                [('partner_id', '=', res_partner_id.id), ('id', '=', contact_line_id)]).write(kw)

    @http.route(['/contact/delete/<int:partner_id>/<int:contact_line_id>'], type='http', auth='user', website=True)
    def emergency_contact_delete(self, partner_id,contact_line_id, **kw):
        res_partner_id = request.env['res.partner'].sudo().search([('id', '=', partner_id)])
        if res_partner_id and contact_line_id and contact_line_id in res_partner_id.emergency_line_ids.ids:
            request.env['emergency.lines'].sudo().search([('partner_id', '=', res_partner_id.id),('id','=',contact_line_id)]).unlink()
        #return request.redirect("/my/account")

    @http.route(['/contact/add/<int:partner_id>'], type='http', auth='user', website=True)
    def emergency_contact_add(self, partner_id, **kw):
        if kw.get('name') or kw.get('contact_number') or kw.get('relationship'):
            res_partner_id = request.env['res.partner'].sudo().search([('id','=',partner_id)])
            if res_partner_id:
                kw.update({
                    'partner_id' : res_partner_id.id
                })
                request.env['emergency.lines'].sudo().create(kw)

    @route(['/my/update/profile/<int:partner_id>'], type='http', auth='user', website=True)
    def update_profile(self,partner_id,document_profile_image, **kw):
        res_partner_id = request.env['res.partner'].sudo().search([('id', '=', partner_id)])
        if res_partner_id:
            bdata = base64.encodestring(document_profile_image.read())
            res_partner_id.image = bdata
        return request.redirect("/my/profile")


    @route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        if "consent" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("consent")
        '''
        if "emotional" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("emotional")
        if "environmental" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("environmental")
        if "financial" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("financial")
        if "intellectual" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("intellectual")
        if "occupational" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("occupational")
        if "physical" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("physical")
        if "social" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("social")
        if "spiritual" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("spiritual")
        if "selfharm" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("selfharm")
        if "taking_meds" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("taking_meds")
        if "treatment" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("treatment")
        if "legalcase" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("legalcase")
        if "selfharm_details" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("selfharm_details")
        if "taking_meds_details" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("taking_meds_details")
        if "treatment_details" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("treatment_details")
        if "legalcase_details" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("legalcase_details")
        if "personal_preference" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("personal_preference")
        if "problem" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("problem")
        if "other_info" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("other_info")
        if "support_ids" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("support_ids")
        '''

        if "birthday" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("birthday")
        if "hmo_id" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("hmo_id")
        if "client_age" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("client_age")
        if "hmo_no" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("hmo_no")
        if "sex" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("sex")
        if "clinic_visited" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("clinic_visited")
        if "marital" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("marital")
        if "philhealthid" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("philhealthid")
        if "source_id" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("source_id")
        if "guardian" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("guardian")
        if "special_priority" not in self.OPTIONAL_BILLING_FIELDS:
            self.OPTIONAL_BILLING_FIELDS.append("special_priority")
        if "name" in self.MANDATORY_BILLING_FIELDS:
            self.MANDATORY_BILLING_FIELDS.remove("name")
        if "firstname" not in self.MANDATORY_BILLING_FIELDS:
            self.MANDATORY_BILLING_FIELDS.append("firstname")
        if "lastname" not in self.MANDATORY_BILLING_FIELDS:
            self.MANDATORY_BILLING_FIELDS.append("lastname")
        if "middlename" not in self.MANDATORY_BILLING_FIELDS:
            self.MANDATORY_BILLING_FIELDS.append("middlename")

        call_super = super(CustomerPortal, self).account(redirect,**post)
        return call_super

    def _prepare_portal_layout_values(self):
        call_super = super(CustomerPortal, self)._prepare_portal_layout_values()

        utm_source_ids = request.env['utm.source'].sudo().search([])
        client_support_ids = request.env['client.support'].sudo().search([])
        hmo_provider_ids = request.env['hmo.provider'].sudo().search([])

        call_super.update({
            'hmo_provider_ids' : hmo_provider_ids,
            'utm_source_ids': utm_source_ids,
            'client_support_ids': client_support_ids
        })
        return call_super