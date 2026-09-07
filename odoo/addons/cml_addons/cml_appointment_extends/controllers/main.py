# -*- coding: utf-8 -*-

from odoo import http,_
from odoo.http import request
from collections import OrderedDict
from odoo.addons.portal.controllers.portal import \
CustomerPortal, pager as portal_pager, get_records_pager
from datetime import datetime
class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id.id
        appointments_upcoming_ids = request.env['clinic.appointment'].sudo().search([('partner_id','=',partner),('session_start','>=', datetime.today().strftime('%Y-%m-%d'))])
        appointments_history_ids = request.env['clinic.appointment'].sudo().search([('partner_id','=',partner),('session_start', '<', datetime.today().strftime('%Y-%m-%d'))])
        values.update({
            'my_appointments_history_count': len(appointments_history_ids),
            'my_appointments_upcoming_count': len(appointments_upcoming_ids),
        })
        return values


    @http.route(['/my/upcoming/appointments/list', '/my/upcoming/appointments/list/page/<int:page>'], type='http', auth='user', website=True)
    def my_upcoming_appointments_lists(self, page=1, sortby=None,filterby=None, **kw):
        searchbar_sortings = {
            'Name': {'label': _('Name'), 'order': 'sequence'},
            'Start': {'label': _('Date'), 'order': 'session_start desc'},
        }
        searchbar_filters = {
            'up_coming_appointment': {'label': _('Up-Coming Appointments'), 'domain': [('session_start','>=', datetime.today().strftime('%Y-%m-%d'))]}
        }
        if not sortby:
            sortby = 'Name'

        if not filterby:
            filterby = 'up_coming_appointment'
        order = searchbar_sortings[sortby]['order']
        domain = searchbar_filters[filterby]['domain']
        domain += [('partner_id','=',http.request.env.user.partner_id.id)]
        appointment_count = http.request.env['clinic.appointment'].sudo().search_count(domain)
        pager = portal_pager(
            url="/my/upcoming/appointments/list",
            total=appointment_count,
            page=page,
            step=10
        )
        appointments = http.request.env['clinic.appointment'].sudo().search(domain, order=order, limit=10, offset=pager['offset'])
        return http.request.render(
            'cml_appointment_extends.template_portal_my_home_menu_upcoing_appointments_lists',
            {
                'docs': appointments,
                'searchbar_sortings': searchbar_sortings,
                'default_url': '/my/upcoming/appointments/list',
                'page_name' : 'appointment_upcoming_list',
                'sortby': sortby,
                'pager': pager,
                'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
                'filterby': filterby,
           }
        )

    @http.route(['/my/appointments/history/list', '/my/appointments/history/list/page/<int:page>'], type='http', auth='user',
                website=True)
    def my_appointments_history_lists(self, page=1, sortby=None, filterby=None, **kw):
        searchbar_sortings = {
            'Name': {'label': _('Name'), 'order': 'sequence'},
            'Start': {'label': _('Date'), 'order': 'session_start desc'},
        }
        searchbar_filters = {
            'history': {'label': _('History'),
                                      'domain': [('session_start', '<', datetime.today().strftime('%Y-%m-%d'))]}
        }
        if not sortby:
            sortby = 'Name'

        if not filterby:
            filterby = 'history'
        order = searchbar_sortings[sortby]['order']
        domain = searchbar_filters[filterby]['domain']
        domain += [('partner_id','=',http.request.env.user.partner_id.id)]
        appointment_count = http.request.env['clinic.appointment'].sudo().search_count(domain)
        pager = portal_pager(
            url="/my/appointments/history/list",
            total=appointment_count,
            page=page,
            step=10
        )
        appointments = http.request.env['clinic.appointment'].sudo().search(domain, order=order, limit=10,
                                                                            offset=pager['offset'])
        return http.request.render(
            'cml_appointment_extends.template_portal_my_home_menu_history_appointments_lists',
            {
                'docs': appointments,
                'searchbar_sortings': searchbar_sortings,
                'default_url': '/my/appointments/history/list',
                'page_name': 'appointment_history_list',
                'sortby': sortby,
                'pager': pager,
                'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
                'filterby': filterby,
            }
        )


    @http.route([
        '''/my/appointments/popup/<int:appoint_id>'''
    ], type='http', auth="public", website=True)
    def appointment_feedback(self, appoint_id=None, **post):
        appointment_id = http.request.env['clinic.appointment'].sudo().search([('id', '=', appoint_id)])
        appointment_id.sudo().write(post)
        url = "/my/appointments/history/list"
        return request.redirect(url)
