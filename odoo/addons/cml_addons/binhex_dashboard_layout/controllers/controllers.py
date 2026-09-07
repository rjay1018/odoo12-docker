# -*- coding: utf-8 -*-
from odoo import http

class BinhexDashboardLayout(http.Controller):
    #Path where the user profile is created.
    @http.route('/my/profile', auth='public',website=True)
    def index(self, **kw):
        return http.request.render('binhex_dashboard_layout.myprofile',{})

    @http.route('/my/prueba', auth='public',website=True)
    def index1(self, **kw):
        return http.request.render('binhex_dashboard_layout.prueba',{})

