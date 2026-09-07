# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo.tools.float_utils import float_round as round
from odoo import api, fields, models, _
from datetime import datetime, time, date
from dateutil.relativedelta import relativedelta
from lxml import etree
import base64
import re
from ast import literal_eval
from odoo import tools
# import odoo.report
import calendar


class Res_Partner(models.Model):
    _inherit = 'res.partner'
    start_date_cust = fields.Date('Start Date')
    end_date_cust = fields.Date('End Date')
    status_paid = fields.Selection([
        ('paid', 'Paid'),
        ('open', 'Unpaid')
    ], string='Status')
    status_paid_vendor = fields.Selection([
        ('paid', 'Paid'),
        ('open', 'Unpaid')
    ], string='Status')

    @api.model
    def _get_domain(self):
        for rec in self:
            return [('show', '=', True), ('type', 'in', ['out_invoice', 'out_refund']), ('state', 'in', ['open', 'paid']),
                    ('partner_id', '=', rec.id)]

    def _get_vendor_domain(self):
        for rec in self:
            return [('type', 'in', ['in_invoice', 'in_refund']), ('state', 'in', ['open', 'paid']),
                    ('partner_id', '=', rec.id), ('show_vendor', '=', True)]

    balance_invoice_ids = fields.One2many(domain=_get_domain)
    supplier_invoice_ids = fields.One2many(domain=_get_vendor_domain)
    start_date_vendor = fields.Date('Start Date')
    end_date_vendor = fields.Date('End Date')

    def action_apply_filter(self):
        for i in self.env['account.invoice'].search(
                [('type', 'in', ['out_invoice', 'out_refund']), ('state', 'in', ['open', 'paid']),
                 ('partner_id', '=', self.id)]):
            if (self.start_date_cust and self.end_date_cust) and self.status_paid:
                if (
                        not i.date_invoice <= self.end_date_cust and not i.date_invoice >= self.start_date_cust) and i.state != self.status_paid:
                    i.show = False
                elif (i.date_invoice <= self.end_date_cust and i.date_invoice >= self.start_date_cust) \
                        and i.state == self.status_paid:
                    i.show = True
                elif (i.date_invoice <= self.end_date_cust and i.date_invoice >= self.start_date_cust) \
                        and i.state != self.status_paid:
                    i.show = False

            elif (self.start_date_cust and self.end_date_cust) and not self.status_paid:
                if not (i.date_invoice <= self.end_date_cust and i.date_invoice >= self.start_date_cust):

                    i.show = False
                elif (i.date_invoice <= self.end_date_cust and i.date_invoice >= self.start_date_cust):

                    i.show = True

            elif (not self.start_date_cust and not self.end_date_cust) and self.status_paid:
                if i.state != self.status_paid:
                    i.show = False
                elif i.state == self.status_paid:
                    i.show = True
            elif (not self.start_date_cust and not self.end_date_cust) and not self.status_paid:
                i.show = True

    def action_remove_filter(self):
        self.start_date_cust = False
        self.end_date_cust = False
        self.status_paid = False
        for i in self.env['account.invoice'].search(
                [('type', 'in', ['out_invoice', 'out_refund']), ('state', 'in', ['open', 'paid']),
                 ('partner_id', '=', self.id)]):
            i.show = True

    def action_apply_filter_vendor(self):
        for i in self.env['account.invoice'].search(
                [('type', 'in', ['in_invoice', 'in_refund']), ('state', 'in', ['open', 'paid']),
                 ('partner_id', '=', self.id)]):
            if (self.start_date_vendor and self.end_date_vendor) and self.status_paid_vendor:
                if (not i.date_invoice <= self.end_date_vendor and not i.date_invoice >= self.start_date_vendor) and \
                        i.state != self.status_paid_vendor:
                    i.show_vendor = False
                elif (i.date_invoice <= self.end_date_vendor and i.date_invoice >= self.start_date_vendor) and \
                        i.state == self.status_paid_vendor:
                    i.show_vendor = True
                elif (i.date_invoice <= self.end_date_vendor and i.date_invoice >= self.start_date_vendor) \
                        and i.state != self.status_paid_vendor:
                    i.show_vendor = False

            elif (self.start_date_vendor and self.end_date_vendor) and not self.status_paid_vendor:
                if not (i.date_invoice <= self.end_date_vendor and i.date_invoice >= self.start_date_vendor):

                    i.show_vendor = False
                elif (i.date_invoice <= self.end_date_vendor and i.date_invoice >= self.start_date_vendor):

                    i.show_vendor = True

            elif (not self.start_date_vendor and not self.end_date_vendor) and self.status_paid_vendor:
                if i.state != self.status_paid_vendor:
                    i.show_vendor = False
                elif i.state == self.status_paid_vendor:
                    i.show_vendor = True
            elif (not self.start_date_vendor and not self.end_date_vendor) and not self.status_paid_vendor:
                i.show_vendor = True

    def action_remove_filter_vendor(self):
        self.start_date_vendor = False
        self.end_date_vendor = False
        self.status_paid_vendor = False
        for i in self.env['account.invoice'].search(
                [('type', 'in', ['in_invoice', 'in_refund']), ('state', 'in', ['open', 'paid']),
                 ('partner_id', '=', self.id), ('show_vendor', '=', True)]):
            i.show_vendor = True


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    show = fields.Boolean(default=True)
    show_vendor = fields.Boolean(default=True)
