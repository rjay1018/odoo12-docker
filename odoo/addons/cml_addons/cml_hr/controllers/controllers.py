# -*- coding: utf-8 -*-
from odoo import http

# class CmlKso/(http.Controller):
#     @http.route('/cml_kso//cml_kso//', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cml_kso//cml_kso//objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('cml_kso/.listing', {
#             'root': '/cml_kso//cml_kso/',
#             'objects': http.request.env['cml_kso/.cml_kso/'].search([]),
#         })

#     @http.route('/cml_kso//cml_kso//objects/<model("cml_kso/.cml_kso/"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cml_kso/.object', {
#             'object': obj
#         })