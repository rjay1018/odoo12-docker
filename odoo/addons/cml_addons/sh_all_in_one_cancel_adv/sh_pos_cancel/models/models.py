# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, _
from odoo.exceptions import ValidationError


class POSOrder(models.Model):
    _inherit = 'pos.order'

    def action_pos_cancel_draft(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_pos_cancel'):
            raise ValidationError(
                _("Enable Configuration for POS Cancel Feature"))
        else:
            for rec in self:
                if rec.company_id.pos_cancel_delivery:
                    if rec.mapped('picking_id'):
                        if rec.mapped('picking_id').mapped('move_ids_without_package'):
                            rec.mapped('picking_id').mapped(
                                'move_ids_without_package').write({'state': 'cancel'})
                            rec.mapped('picking_id').mapped('move_ids_without_package').mapped(
                                'move_line_ids').write({'state': 'cancel'})
                        rec._sh_unreseve_qty()
                        rec.mapped('picking_id').write(
                            {'state': 'draft', 'show_mark_as_todo': True})

                if rec.company_id.pos_cancel_invoice:

                    if rec.mapped('invoice_id'):
                        if rec.mapped('invoice_id').mapped('move_id'):
                            move = rec.mapped('invoice_id').mapped('move_id')
                            move_line_ids = move.mapped('line_ids')

                            reconcile_ids = []
                            if move_line_ids:
                                reconcile_ids = move_line_ids.mapped('id')

                            reconcile_lines = self.env['account.partial.reconcile'].search(
                                ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                            if reconcile_lines:
                                reconcile_lines.unlink()

                            move.mapped(
                                'line_ids.analytic_line_ids').unlink()
                            move_line_ids.write(
                                {'parent_state': 'draft'})
                            move.write({'state': 'draft'})

                        rec.mapped('invoice_id').write(
                            {'state': 'draft'})

                if rec.mapped('statement_ids'):
                    statement_ids = rec.mapped('statement_ids')

                    journal_entry_ids = statement_ids.mapped(
                        'journal_entry_ids')
                    reconcile_ids = journal_entry_ids.mapped('id')

                    reconcile_lines = self.env['account.partial.reconcile'].search(
                        ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                    if reconcile_lines:
                        reconcile_lines.unlink()

                    statement_ids.mapped('journal_entry_ids').mapped(
                        'move_id').write({'state': 'draft'})
                    statement_ids.mapped('journal_entry_ids').mapped(
                        'move_id').unlink()
                    statement_ids.mapped('journal_entry_ids').write(
                        {'state': 'draft'})
                    statement_ids.mapped('journal_entry_ids').unlink()
                rec.write({'state': 'draft'})

    def action_pos_cancel_delete(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_pos_cancel'):
            raise ValidationError(
                _("Enable Configuration for POS Cancel Feature"))
        else:
            for rec in self:
                if rec.company_id.pos_cancel_delivery:

                    if rec.mapped('picking_id'):
                        if rec.mapped('picking_id').mapped('move_ids_without_package'):
                            rec.mapped('picking_id').mapped(
                                'move_ids_without_package').write({'state': 'draft'})
                            rec.mapped('picking_id').mapped('move_ids_without_package').mapped(
                                'move_line_ids').write({'state': 'draft'})
                            rec._sh_unreseve_qty()
                            rec.mapped('picking_id').mapped(
                                'move_ids_without_package').unlink()
                            rec.mapped('picking_id').mapped(
                                'move_ids_without_package').mapped('move_line_ids').unlink()

                        rec.mapped('picking_id').write(
                            {'state': 'draft'})
                        rec.mapped('picking_id').unlink()

                if rec.company_id.pos_cancel_invoice:

                    if rec.mapped('invoice_id'):
                        if rec.mapped('invoice_id').mapped('move_id'):
                            move = rec.mapped('invoice_id').mapped('move_id')
                            move_line_ids = move.mapped('line_ids')

                            reconcile_ids = []
                            if move_line_ids:
                                reconcile_ids = move_line_ids.mapped('id')

                            reconcile_lines = self.env['account.partial.reconcile'].search(
                                ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                            if reconcile_lines:
                                reconcile_lines.unlink()

                            move.mapped(
                                'line_ids.analytic_line_ids').unlink()
                            move_line_ids.write(
                                {'parent_state': 'draft'})
                            move.write({'state': 'draft'})

                        rec.mapped('invoice_id').write(
                            {'state': 'draft', 'move_name': ''})
                        rec.mapped('invoice_id').unlink()

                if rec.mapped('statement_ids'):
                    statement_ids = rec.mapped('statement_ids')

                    journal_entry_ids = statement_ids.mapped(
                        'journal_entry_ids')
                    reconcile_ids = journal_entry_ids.mapped('id')

                    reconcile_lines = self.env['account.partial.reconcile'].search(
                        ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                    if reconcile_lines:
                        reconcile_lines.unlink()

                    statement_ids.mapped('journal_entry_ids').mapped(
                        'move_id').write({'state': 'draft'})
                    statement_ids.mapped('journal_entry_ids').mapped(
                        'move_id').unlink()
                    statement_ids.mapped('journal_entry_ids').write(
                        {'state': 'draft'})
                    statement_ids.mapped('journal_entry_ids').unlink()

                rec.write({'state': 'cancel'})
            for rec in self:
                rec.unlink()

    def _sh_unreseve_qty(self):
        for move_line in self.mapped('picking_id').mapped('move_ids_without_package').mapped('move_line_ids'):
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

    def sh_cancel(self):

        if self.company_id.pos_cancel_delivery:
            if self.company_id.pos_operation_type == 'cancel_draft':
                if self.mapped('picking_id'):
                    if self.mapped('picking_id').mapped('move_ids_without_package'):
                        self.mapped('picking_id').mapped(
                            'move_ids_without_package').write({'state': 'cancel'})
                        self.mapped('picking_id').mapped('move_ids_without_package').mapped(
                            'move_line_ids').write({'state': 'cancel'})
                    self._sh_unreseve_qty()
                    self.mapped('picking_id').write(
                        {'state': 'draft', 'show_mark_as_todo': True})

            elif self.company_id.pos_operation_type == 'cancel_delete':
                if self.mapped('picking_id'):
                    if self.mapped('picking_id').mapped('move_ids_without_package'):
                        self.mapped('picking_id').mapped(
                            'move_ids_without_package').write({'state': 'draft'})
                        self.mapped('picking_id').mapped('move_ids_without_package').mapped(
                            'move_line_ids').write({'state': 'draft'})
                        self._sh_unreseve_qty()
                        self.mapped('picking_id').mapped(
                            'move_ids_without_package').unlink()
                        self.mapped('picking_id').mapped(
                            'move_ids_without_package').mapped('move_line_ids').unlink()

                    self.mapped('picking_id').write(
                        {'state': 'draft'})
                    self.mapped('picking_id').unlink()

        if self.company_id.pos_cancel_invoice:

            if self.mapped('invoice_id'):
                if self.mapped('invoice_id').mapped('move_id'):
                    move = self.mapped('invoice_id').mapped('move_id')
                    move_line_ids = move.mapped('line_ids')

                    reconcile_ids = []
                    if move_line_ids:
                        reconcile_ids = move_line_ids.mapped('id')

                    reconcile_lines = self.env['account.partial.reconcile'].search(
                        ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                    if reconcile_lines:
                        reconcile_lines.unlink()

                    move.mapped('line_ids.analytic_line_ids').unlink()
                    move_line_ids.write({'parent_state': 'draft'})
                    move.write({'state': 'draft'})

                if self.company_id.pos_operation_type == 'cancel_draft':
                    self.mapped('invoice_id').write({'state': 'draft'})
                elif self.company_id.pos_operation_type == 'cancel_delete':
                    self.mapped('invoice_id').write(
                        {'state': 'draft', 'move_name': ''})
                    self.mapped('invoice_id').unlink()

        if self.mapped('statement_ids'):
            statement_ids = self.mapped('statement_ids')

            journal_entry_ids = statement_ids.mapped('journal_entry_ids')
            reconcile_ids = journal_entry_ids.mapped('id')

            reconcile_lines = self.env['account.partial.reconcile'].search(
                ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
            if reconcile_lines:
                reconcile_lines.unlink()

            statement_ids.mapped('journal_entry_ids').mapped(
                'move_id').write({'state': 'draft'})
            statement_ids.mapped('journal_entry_ids').mapped(
                'move_id').unlink()
            statement_ids.mapped('journal_entry_ids').write(
                {'state': 'draft'})
            statement_ids.mapped('journal_entry_ids').unlink()

        if self.company_id.pos_operation_type == 'cancel_draft':
            self.write({'state': 'draft'})
        elif self.company_id.pos_operation_type == 'cancel_delete':
            self.write({'state': 'cancel'})
            self.unlink()
            return {
                'name': 'POS Order',
                'type': 'ir.actions.act_window',
                'res_model': 'pos.order',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'target': 'current',
            }
