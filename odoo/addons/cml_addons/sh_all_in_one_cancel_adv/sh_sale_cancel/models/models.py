# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, api, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _check_stock_installed(self):
        stock_app = self.env['ir.module.module'].search(
            [('name', '=', 'stock')], limit=1)
        if stock_app.state != 'installed':
            return False
        else:
            return True

    @api.multi
    def action_sale_cancel(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_sale_cancel'):
            raise ValidationError(
                _("Enable Configuration for Sales Cancel Feature"))
        else:
            for rec in self:
                if rec.company_id.cancel_delivery and self._check_stock_installed():
    
                    if rec.mapped('picking_ids'):
                        if rec.mapped('picking_ids').mapped('move_ids_without_package'):
                            rec.mapped('picking_ids').mapped(
                                'move_ids_without_package').write({'state': 'cancel'})
                            rec.mapped('picking_ids').mapped('move_ids_without_package').mapped(
                                'move_line_ids').write({'state': 'cancel'})
                        rec._sh_unreseve_qty()
                        rec.mapped('picking_ids').write(
                            {'state': 'cancel'})
    
                if rec.company_id.cancel_invoice:
                    if rec.mapped('invoice_ids'):
                        if rec.mapped('invoice_ids').mapped('move_id'):
                            move = rec.mapped(
                                'invoice_ids').mapped('move_id')
                            move_line_ids = move.mapped('line_ids')
                            reconcile_ids = []
                            if move_line_ids:
                                reconcile_ids = move_line_ids.mapped('id')
                            reconcile_lines = self.env['account.partial.reconcile'].search(
                                ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                            if reconcile_lines:
                                reconcile_lines.unlink()
                            if rec.mapped('invoice_ids').mapped('payment_ids'):
                                payment_ids = rec.mapped(
                                    'invoice_ids').mapped('payment_ids')
                                if payment_ids.mapped('move_line_ids'):
                                    payment_lines = payment_ids.mapped('move_line_ids')
                                    reconcile_ids = payment_lines.mapped('id')
    
                            reconcile_lines = self.env['account.partial.reconcile'].search(
                                ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                            if reconcile_lines:
                                reconcile_lines.unlink()
                            move.mapped(
                                'line_ids.analytic_line_ids').unlink()
    
                            move_line_ids.write({'state': 'draft'})
                            move.write({'state': 'draft'})
    
                            if rec.mapped('invoice_ids').mapped('payment_ids'):
                                payment_ids = rec.mapped(
                                    'invoice_ids').mapped('payment_ids')
                                payment_ids.mapped('move_line_ids').mapped(
                                    'move_id').write({'state': 'draft'})
                                payment_ids.mapped(
                                    'move_line_ids').write({'state': 'draft'})
                                payment_ids.mapped('move_line_ids').unlink()
                                payment_ids.mapped('move_line_ids').mapped('move_id').unlink()
                                payment_ids.write({'state': 'cancelled'})
                        rec.mapped('invoice_ids').write({'state': 'cancel'})
                rec.write({'state': 'cancel'})

    @api.multi
    def action_sale_cancel_draft(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_sale_cancel'):
            raise ValidationError(
                _("Enable Configuration for Sales Cancel Feature"))
        else:
            for rec in self:
                if rec.company_id.cancel_delivery and self._check_stock_installed():
    
                    if rec.mapped('picking_ids'):
                        if rec.mapped('picking_ids').mapped('move_ids_without_package'):
                            rec.mapped('picking_ids').mapped(
                                'move_ids_without_package').write({'state': 'draft'})
                            rec.mapped('picking_ids').mapped('move_ids_without_package').mapped(
                                'move_line_ids').write({'state': 'draft'})
                        rec._sh_unreseve_qty()
                        rec.mapped('picking_ids').write(
                            {'state': 'draft', 'show_mark_as_todo': True})
    
                if rec.company_id.cancel_invoice:
                    if rec.mapped('invoice_ids'):
                        if rec.mapped('invoice_ids').mapped('move_id'):
                            move = rec.mapped(
                                'invoice_ids').mapped('move_id')
                            move_line_ids = move.mapped('line_ids')
    
                            reconcile_ids = []
                            if move_line_ids:
                                reconcile_ids = move_line_ids.mapped('id')
    
                            reconcile_lines = self.env['account.partial.reconcile'].search(
                                ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                            if reconcile_lines:
                                reconcile_lines.unlink()
    
                            if rec.mapped('invoice_ids').mapped('payment_ids'):
                                payment_ids = rec.mapped(
                                    'invoice_ids').mapped('payment_ids')
                                if payment_ids.mapped('move_line_ids'):
                                    payment_lines = payment_ids.mapped('move_line_ids')
                                    reconcile_ids = payment_lines.mapped('id')
    
                            reconcile_lines = self.env['account.partial.reconcile'].search(
                                ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                            if reconcile_lines:
                                reconcile_lines.unlink()
                            move.mapped(
                                'line_ids.analytic_line_ids').unlink()
    
                            move_line_ids.write({'state': 'draft'})
                            move.write({'state': 'draft'})
    
                            if rec.mapped('invoice_ids').mapped('payment_ids'):
                                payment_ids = rec.mapped(
                                    'invoice_ids').mapped('payment_ids')
                                payment_ids.mapped('move_line_ids').mapped(
                                    'move_id').write({'state': 'draft'})
                                payment_ids.mapped(
                                    'move_line_ids').write({'state': 'draft'})
                                payment_ids.mapped('move_line_ids').unlink()
                                payment_ids.mapped('move_line_ids').mapped('move_id').unlink()
                                payment_ids.write(
                                    {'state': 'draft', 'move_name': ''})
                                payment_ids.unlink()
                        rec.mapped('invoice_ids').write(
                            {'state': 'draft', 'move_name': ''})
                rec.write({'state': 'draft'})

    @api.multi
    def action_sale_cancel_delete(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_sale_cancel'):
            raise ValidationError(
                _("Enable Configuration for Sales Cancel Feature"))
        else:
            for rec in self:
                if rec.company_id.cancel_delivery and self._check_stock_installed():
    
                    if rec.mapped('picking_ids'):
                        if rec.mapped('picking_ids').mapped('move_ids_without_package'):
                            rec.mapped('picking_ids').mapped(
                                'move_ids_without_package').write({'state': 'draft'})
                            rec.mapped('picking_ids').mapped('move_ids_without_package').mapped(
                                'move_line_ids').write({'state': 'draft'})
                            rec._sh_unreseve_qty()
                            rec.mapped('picking_ids').mapped(
                                'move_ids_without_package').unlink()
                            rec.mapped('picking_ids').mapped(
                                'move_ids_without_package').mapped('move_line_ids').unlink()
    
                        rec.mapped('picking_ids').write(
                            {'state': 'draft'})
                        rec.mapped('picking_ids').unlink()
    
                if rec.company_id.cancel_invoice:
    
                    if rec.mapped('invoice_ids'):
                        if rec.mapped('invoice_ids').mapped('move_id'):
                            move = rec.mapped(
                                'invoice_ids').mapped('move_id')
                            move_line_ids = move.mapped('line_ids')
    
                            reconcile_ids = []
                            if move_line_ids:
                                reconcile_ids = move_line_ids.mapped('id')
    
                            reconcile_lines = self.env['account.partial.reconcile'].search(
                                ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                            if reconcile_lines:
                                reconcile_lines.unlink()
    
                            if rec.mapped('invoice_ids').mapped('payment_ids'):
                                payment_ids = rec.mapped(
                                    'invoice_ids').mapped('payment_ids')
                                if payment_ids.mapped('move_line_ids'):
                                    payment_lines = payment_ids.mapped('move_line_ids')
                                    reconcile_ids = payment_lines.mapped('id')
    
                            reconcile_lines = self.env['account.partial.reconcile'].search(
                                ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                            if reconcile_lines:
                                reconcile_lines.unlink()
                            move.mapped(
                                'line_ids.analytic_line_ids').unlink()
    
                            move_line_ids.write({'state': 'draft'})
                            move.write({'state': 'draft'})
    
                            if rec.mapped('invoice_ids').mapped('payment_ids'):
                                payment_ids = rec.mapped(
                                    'invoice_ids').mapped('payment_ids')
                                payment_ids.mapped('move_line_ids').mapped(
                                    'move_id').write({'state': 'draft'})
                                payment_ids.mapped(
                                    'move_line_ids').write({'state': 'draft'})
                                payment_ids.mapped('move_line_ids').unlink()
                                payment_ids.mapped('move_line_ids').mapped('move_id').unlink()
    
                                payment_ids.write(
                                    {'state': 'draft', 'move_name': ''})
                                payment_ids.unlink()
    
                        rec.mapped('invoice_ids').write(
                            {'state': 'draft', 'move_name': ''})
                        rec.mapped('invoice_ids').unlink()
    
                rec.write({'state': 'cancel'})
                rec.unlink()

    def _sh_unreseve_qty(self):
        for move_line in self.mapped('picking_ids').mapped('move_ids_without_package').mapped('move_line_ids'):
            # unreserve qty
            quant = self.env['stock.quant'].search([('location_id', '=', move_line.location_id.id),
                                                           ('product_id', '=',
                                                            move_line.product_id.id),
                                                           ('lot_id', '=', move_line.lot_id.id)], limit=1)

            if quant:
                quant.write({'quantity': quant.quantity + move_line.qty_done})

            quant = self.env['stock.quant'].search([('location_id', '=', move_line.location_dest_id.id),
                                                           ('product_id', '=',
                                                            move_line.product_id.id),
                                                           ('lot_id', '=', move_line.lot_id.id)], limit=1)

            if quant:
                quant.write({'quantity': quant.quantity - move_line.qty_done})

    @api.multi
    def sh_cancel(self):

        if self.company_id.cancel_delivery and self._check_stock_installed():
            if self.company_id.operation_type == 'cancel':
                if self.mapped('picking_ids'):
                    if self.mapped('picking_ids').mapped('move_ids_without_package'):
                        self.mapped('picking_ids').mapped(
                            'move_ids_without_package').write({'state': 'cancel'})
                        self.mapped('picking_ids').mapped('move_ids_without_package').mapped(
                            'move_line_ids').write({'state': 'cancel'})
                    self._sh_unreseve_qty()
                    self.mapped('picking_ids').write(
                        {'state': 'cancel'})

            elif self.company_id.operation_type == 'cancel_draft':
                if self.mapped('picking_ids'):
                    if self.mapped('picking_ids').mapped('move_ids_without_package'):
                        self.mapped('picking_ids').mapped(
                            'move_ids_without_package').write({'state': 'draft'})
                        self.mapped('picking_ids').mapped('move_ids_without_package').mapped(
                            'move_line_ids').write({'state': 'draft'})
                    self._sh_unreseve_qty()
                    self.mapped('picking_ids').write(
                        {'state': 'draft', 'show_mark_as_todo': True})

            elif self.company_id.operation_type == 'cancel_delete':
                if self.mapped('picking_ids'):
                    if self.mapped('picking_ids').mapped('move_ids_without_package'):
                        self.mapped('picking_ids').mapped(
                            'move_ids_without_package').write({'state': 'draft'})
                        self.mapped('picking_ids').mapped('move_ids_without_package').mapped(
                            'move_line_ids').write({'state': 'draft'})
                        self._sh_unreseve_qty()
                        self.mapped('picking_ids').mapped(
                            'move_ids_without_package').unlink()
                        self.mapped('picking_ids').mapped(
                            'move_ids_without_package').mapped('move_line_ids').unlink()

                    self.mapped('picking_ids').write(
                        {'state': 'draft'})
                    self.mapped('picking_ids').unlink()

        if self.company_id.cancel_invoice:

            if self.mapped('invoice_ids'):
                if self.mapped('invoice_ids').mapped('move_id'):
                    move = self.mapped('invoice_ids').mapped('move_id')
                    move_line_ids = move.mapped('line_ids')

                    reconcile_ids = []
                    if move_line_ids:
                        reconcile_ids = move_line_ids.mapped('id')

                    reconcile_lines = self.env['account.partial.reconcile'].search(
                        ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                    if reconcile_lines:
                        reconcile_lines.unlink()

                    if self.mapped('invoice_ids').mapped('payment_ids'):
                        payment_ids = self.mapped(
                            'invoice_ids').mapped('payment_ids')
                        if payment_ids.mapped('move_line_ids'):
                            payment_lines = payment_ids.mapped('move_line_ids')
                            reconcile_ids = payment_lines.mapped('id')

                    reconcile_lines = self.env['account.partial.reconcile'].search(
                        ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                    if reconcile_lines:
                        reconcile_lines.unlink()
                    move.mapped('line_ids.analytic_line_ids').unlink()

                    move_line_ids.write({'state': 'draft'})
                    move.write({'state': 'draft'})

                    if self.mapped('invoice_ids').mapped('payment_ids'):
                        payment_ids = self.mapped(
                            'invoice_ids').mapped('payment_ids')
                        payment_ids.mapped('move_line_ids').mapped(
                            'move_id').write({'state': 'draft'})
                        payment_ids.mapped(
                            'move_line_ids').write({'state': 'draft'})
                        payment_ids.mapped('move_line_ids').unlink()
                        payment_ids.mapped('move_line_ids').mapped('move_id').unlink()
                        if self.company_id.operation_type == 'cancel':
                            payment_ids.write({'state': 'cancelled'})
                        elif self.company_id.operation_type == 'cancel_draft':
                            payment_ids.write(
                                {'state': 'draft', 'move_name': ''})
                            payment_ids.unlink()
                        elif self.company_id.operation_type == 'cancel_delete':
                            payment_ids.write(
                                {'state': 'draft', 'move_name': ''})
                            payment_ids.unlink()

                if self.company_id.operation_type == 'cancel':
                    self.mapped('invoice_ids').write(
                        {'state': 'cancel'})
                elif self.company_id.operation_type == 'cancel_draft':
                    self.mapped('invoice_ids').write(
                        {'state': 'draft', 'move_name': ''})
                elif self.company_id.operation_type == 'cancel_delete':
                    self.mapped('invoice_ids').write(
                        {'state': 'draft', 'move_name': ''})
                    self.mapped('invoice_ids').unlink()

        if self.company_id.operation_type == 'cancel':
            self.write({'state': 'cancel'})
        elif self.company_id.operation_type == 'cancel_draft':
            self.write({'state': 'draft'})
        elif self.company_id.operation_type == 'cancel_delete':
            self.write({'state': 'cancel'})
            self.unlink()
            return {
                'name': 'Quotations',
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'view_type': 'form',
                'view_mode': 'tree,kanban,form,calendar,pivot,graph,activity',
                'target': 'current',
                'context': {'search_default_my_quotation': 1}
            }
