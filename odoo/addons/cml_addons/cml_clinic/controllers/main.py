from odoo import http
from odoo.http import request


class Registration(http.Controller):

    @http.route('/hello', type="http", website=True, auth='public')
    def hello_registration(self, **kw):
        sources = request.env['utm.source'].sudo().search([])
        support = request.env['client.support'].sudo().search([])
        return request.render("cml_clinic.create_client", {
            'sources': sources,
            'support': support,
        })

    @http.route('/create/client', type="http", website=True, auth='public')
    def create_client(self, **kw):
        request.env['res.partner'].sudo().create(kw)
        return request.render("cml_clinic.registartion_thanks", {})
