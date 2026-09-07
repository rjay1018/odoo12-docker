from odoo import http,_
from odoo.http import request
from collections import OrderedDict
from datetime import datetime
from odoo.addons.portal.controllers.portal import \
CustomerPortal, pager as portal_pager, get_records_pager


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        assessments = http.request.env['survey.user_input'].sudo().search([('partner_id','=',partner.id),('state','!=','new')])
        upcoming_assessment_count = http.request.env['survey.user_input'].sudo().search([('partner_id','=',partner.id),('state','=','new')])
        values.update({
            'assessment_count': len(assessments),
            'upcoming_assessment_count' : len(upcoming_assessment_count)
        })
        return values

    @http.route(['/assessments/list', '/assessments/list/page/<int:page>'], type='http', auth='user', website=True)
    def my_assessments_lists(self, page=1, sortby=None,filterby=None, **kw):
        searchbar_sortings = {
            'Date': {'label': _('Date'), 'order': 'date_create desc'},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }
        if not sortby:
            sortby = 'Date'

        if not filterby:
            filterby = 'all'
        order = searchbar_sortings[sortby]['order']
        domain = searchbar_filters[filterby]['domain']
        domain += [('partner_id','=',http.request.env.user.partner_id.id),('state','!=','new')]
        assessment_count = http.request.env['survey.user_input'].sudo().search_count(domain)
        pager = portal_pager(
            url="/assessments/list",
            total=assessment_count,
            page=page,
            step=10
        )
        assessments = http.request.env['survey.user_input'].sudo().search(domain, order=order, limit=10, offset=pager['offset'])
        values = self._prepare_portal_layout_values()
        values.update({
                'docs': assessments,
                'page_name': 'assessment_list',
                'searchbar_sortings': searchbar_sortings,
                'default_url': '/assessments/list',
                'sortby': sortby,
                'pager': pager,
                'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
                'filterby': filterby,
           })
        return http.request.render('cml_assesment_extend.template_portal_my_home_menu_assessments_lists',values)

    @http.route(['/upcoming/assessments/list', '/upcoming/assessments/list/page/<int:page>'], type='http', auth='user', website=True)
    def my_upcoming_assessments_lists(self, page=1, sortby=None, filterby=None, **kw):
        searchbar_sortings = {
            'Date': {'label': _('Date'), 'order': 'date_create desc'},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }
        if not sortby:
            sortby = 'Date'

        if not filterby:
            filterby = 'all'
        order = searchbar_sortings[sortby]['order']
        domain = searchbar_filters[filterby]['domain']
        domain += [('partner_id', '=', http.request.env.user.partner_id.id),('state','=','new')]
        upcoming_assessment_count = http.request.env['survey.user_input'].sudo().search_count(domain)
        pager = portal_pager(
            url="/upcoming/assessments/list",
            total=upcoming_assessment_count,
            page=page,
            step=10
        )
        upcoming_assessments = http.request.env['survey.user_input'].sudo().search(domain, order=order, limit=10,
                                                                   offset=pager['offset'])
        values = self._prepare_portal_layout_values()
        values.update({
            'docs': upcoming_assessments,
            'page_name': 'upcoming_assessment_list',
            'searchbar_sortings': searchbar_sortings,
            'default_url': '/upcoming/assessments/list',
            'sortby': sortby,
            'pager': pager,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
        return http.request.render('cml_assesment_extend.template_portal_my_home_menu_upcoming_assessments_lists', values)