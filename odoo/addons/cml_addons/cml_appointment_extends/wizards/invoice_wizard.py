# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions,_
from odoo.exceptions import ValidationError, UserError


class Multi_Service(models.TransientModel):
    _name = 'multi.service.invoice'

    appoint_id = fields.Many2one(
        'clinic.appointment'
    )
    multi_service_ids = fields.One2many(
        'cml.multi.service.line',
        'appoint_id',
        related="appoint_id.multi_service_ids",
        readonly=False,
    )
    available_session = fields.Float(
        string="Available Session",
        readonly=True
    )

    def action_create_invoice(self):
        invoice = self.appoint_id.action_create_invoice()
        for line in invoice.invoice_line_ids:
            li = self.multi_service_ids.filtered(lambda l:l.service_id.id == line.product_id.id)
            for l in li:
                l.invoiced_qty += line.quantity

    def actin_apply_free_session(self):
        active_id = self._context.get('active_id')
        if active_id:
            order = self.env['clinic.appointment'].browse(active_id)
            for rec in order:
                if any(i.is_free_session_line for i in rec.multi_service_ids):
                    raise ValidationError(_(
                        'You don\'t have Free Session!'))
                if rec.partner_id:
                    for membership in rec.partner_id.member_lines:
                        if membership.date_to > fields.Date.today():
                            if membership.is_apply_free_session:
                                if membership.used_free_session < membership.free_session_number:
                                    if rec.product_id.id in membership.membership_id.allow_free_session_product_ids.ids:
                                        vals = {
                                            'appoint_id': order.id,
                                            'service_id': membership.membership_id.free_product_id.id,
                                            'unit_price': rec.product_id.lst_price,
                                            'is_free_session_line': True,
                                            'qty': -1,
                                            'qty_to_invoice': -1,
                                        }
                                        self.env['cml.multi.service.line'].create(vals)
                                        membership.used_free_session += 1
        return {
            'type': 'ir.actions.act_window',
            'name': ('Multi Invoice'),
            'res_model': 'multi.service.invoice',
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

    @api.model
    def default_get(self, fields_list):
        call_super = super(Multi_Service, self).default_get(fields_list)
        active_id = self._context.get('active_id')
        if active_id:
            order = self.env['clinic.appointment'].browse(active_id)
            # order = self.env['clinic.appointment'].search([('id', '=', active_id)])
            order.multi_service_ids._set_invoice_qty()
            call_super['appoint_id'] = active_id
            call_super['available_session'] = order.partner_id.total_available_session

        return call_super
