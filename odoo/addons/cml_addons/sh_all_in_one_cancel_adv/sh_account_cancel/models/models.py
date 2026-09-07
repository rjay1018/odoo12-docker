# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, api, _
from odoo.exceptions import ValidationError


class Payment(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def action_payment_cancel(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_account_cancel'):
            raise ValidationError(
                _("Enable Configuration for Account Cancel Feature"))
        else:
            for rec in self:
                if rec.mapped('move_line_ids'):
                    payment_lines = rec.mapped('move_line_ids')
                    reconcile_ids = payment_lines.mapped('id')
    
                    reconcile_lines = self.env['account.partial.reconcile'].search(
                        ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                    if reconcile_lines:
                        reconcile_lines.unlink()
                rec.mapped('move_line_ids').mapped(
                    'move_id').write({'state': 'draft'})
                rec.mapped('move_line_ids').mapped('move_id').unlink()
                rec.mapped('move_line_ids').write({'state': 'draft'})
                rec.mapped('move_line_ids').unlink()
                rec.write({'state': 'cancelled'})

    @api.multi
    def action_payment_cancel_draft(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_account_cancel'):
            raise ValidationError(
                _("Enable Configuration for Account Cancel Feature"))
        else:
            for rec in self:
                if rec.mapped('move_line_ids'):
                    payment_lines = rec.mapped('move_line_ids')
                    reconcile_ids = payment_lines.mapped('id')
                    reconcile_lines = self.env['account.partial.reconcile'].search(
                        ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                    if reconcile_lines:
                        reconcile_lines.unlink()
    
                rec.mapped('move_line_ids').mapped(
                    'move_id').write({'state': 'draft'})
                rec.mapped('move_line_ids').mapped('move_id').unlink()
                rec.mapped('move_line_ids').write({'state': 'draft'})
                rec.mapped('move_line_ids').unlink()
                rec.write({'state': 'draft', 'move_name': ''})

    @api.multi
    def action_payment_cancel_delete(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_account_cancel'):
            raise ValidationError(
                _("Enable Configuration for Account Cancel Feature"))
        else:
            for rec in self:
    
                if rec.mapped('move_line_ids'):
                    payment_lines = rec.mapped('move_line_ids')
                    reconcile_ids = payment_lines.mapped('id')
                    reconcile_lines = self.env['account.partial.reconcile'].search(
                        ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                    if reconcile_lines:
                        reconcile_lines.unlink()
    
                rec.mapped('move_line_ids').mapped(
                    'move_id').write({'state': 'draft'})
                rec.mapped('move_line_ids').mapped('move_id').unlink()
                rec.mapped('move_line_ids').write({'state': 'draft'})
                rec.mapped('move_line_ids').unlink()
    
                rec.write({'state': 'draft', 'move_name': ''})
                rec.unlink()

    @api.multi
    def sh_cancel(self):

        if self.mapped('move_line_ids'):
            payment_lines = self.mapped('move_line_ids')
            reconcile_ids = payment_lines.mapped('id')

            reconcile_lines = self.env['account.partial.reconcile'].search(
                ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
            if reconcile_lines:
                reconcile_lines.unlink()

        self.mapped('move_line_ids').mapped(
            'move_id').write({'state': 'draft'})
        self.mapped('move_line_ids').mapped('move_id').unlink()
        self.mapped('move_line_ids').write({'state': 'draft'})
        self.mapped('move_line_ids').unlink()

        if self.company_id.payment_operation_type == 'cancel':
            self.write({'state': 'cancelled'})
        elif self.company_id.payment_operation_type == 'cancel_draft':
            self.write({'state': 'draft', 'move_name': ''})
        elif self.company_id.payment_operation_type == 'cancel_delete':
            self.write({'state': 'draft', 'move_name': ''})
            self.unlink()
            return {
                'name': 'Payments',
                'type': 'ir.actions.act_window',
                'res_model': 'account.payment',
                'view_type': 'form',
                'view_mode': 'tree,kanban,form,graph',
                'target': 'current',
            }


class Journal(models.Model):
    _inherit = 'account.move'

    @api.multi
    def sh_cancel(self):
        move = self
        move_line_ids = move.mapped('line_ids')
        reconcile_ids = []
        if move_line_ids:
            reconcile_ids = move_line_ids.mapped('id')
            reconcile_lines = self.env['account.partial.reconcile'].search(
                ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
            if reconcile_lines:
                reconcile_lines.unlink()

        move_line_ids.write({'state': 'draft'})
        move.write({'state': 'draft'})

    @api.multi
    def action_journal_cancel_draft(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_account_cancel'):
            raise ValidationError(
                _("Enable Configuration for Account Cancel Feature"))
        else:
            for rec in self:
                move = rec
                move_line_ids = move.mapped('line_ids')
                reconcile_ids = []
                if move_line_ids:
                    reconcile_ids = move_line_ids.mapped('id')
                    reconcile_lines = self.env['account.partial.reconcile'].search(
                        ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                    if reconcile_lines:
                        reconcile_lines.unlink()
                move_line_ids.write({'state': 'draft'})
                move.write({'state': 'draft'})

    @api.multi
    def action_journal_cancel_delete(self):
        for rec in self:
            move = rec
            move_line_ids = move.mapped('line_ids')
            reconcile_ids = []
            if move_line_ids:
                reconcile_ids = move_line_ids.mapped('id')
                reconcile_lines = self.env['account.partial.reconcile'].search(
                    ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                if reconcile_lines:
                    reconcile_lines.unlink()
            move_line_ids.write({'state': 'draft'})
            move.write({'state': 'draft'})
            move_line_ids.unlink()
            move.unlink()


class Invoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_cancel(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_account_cancel'):
            raise ValidationError(
                _("Enable Configuration for Account Cancel Feature"))
        else:
            for rec in self:
    
                move = rec.mapped('move_id')
                move_line_ids = move.mapped('line_ids')
                reconcile_ids = []
                if move_line_ids:
                    reconcile_ids = move_line_ids.mapped('id')
                reconcile_lines = self.env['account.partial.reconcile'].search(
                    ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                if reconcile_lines:
                    reconcile_lines.unlink()
    
                if rec.mapped('payment_ids'):
                    payment_ids = rec.mapped('payment_ids')
                    if payment_ids.mapped('move_line_ids'):
                        payment_lines = payment_ids.mapped('move_line_ids')
                        reconcile_ids = payment_lines.mapped('id')
    
                        reconcile_lines = self.env['account.partial.reconcile'].search(
                            ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                        if reconcile_lines:
                            reconcile_lines.unlink()
                        move.mapped('line_ids.analytic_line_ids').unlink()
    
                if rec.mapped('payment_ids'):
                    payment_ids = rec.mapped('payment_ids')
                    payment_ids.mapped('move_line_ids').mapped(
                        'move_id').write({'state': 'draft'})
                    payment_ids.mapped('move_line_ids').mapped('move_id').unlink()
                    payment_ids.mapped(
                        'move_line_ids').write({'state': 'draft'})
                    payment_ids.mapped('move_line_ids').unlink()
    
                    if rec.company_id.payment_operation_type == 'cancel':
                        payment_ids.write({'state': 'cancelled'})
                    elif rec.company_id.payment_operation_type == 'cancel_draft':
                        payment_ids.write(
                            {'state': 'draft', 'move_name': ''})
                    elif rec.company_id.payment_operation_type == 'cancel_delete':
                        payment_ids.write(
                            {'state': 'draft', 'move_name': ''})
                        payment_ids.unlink()
    
                move_line_ids.write({'state': 'draft'})
                move.write({'state': 'draft'})
    
                rec.write({'state': 'cancel'})

    @api.multi
    def action_invoice_cancel_draft(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_account_cancel'):
            raise ValidationError(
                _("Enable Configuration for Account Cancel Feature"))
        else:
            for rec in self:
    
                move = rec.mapped('move_id')
                move_line_ids = move.mapped('line_ids')
                reconcile_ids = []
                if move_line_ids:
                    reconcile_ids = move_line_ids.mapped('id')
                reconcile_lines = self.env['account.partial.reconcile'].search(
                    ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                if reconcile_lines:
                    reconcile_lines.unlink()
    
                if rec.mapped('payment_ids'):
                    payment_ids = rec.mapped('payment_ids')
                    if payment_ids.mapped('move_line_ids'):
                        payment_lines = payment_ids.mapped('move_line_ids')
                        reconcile_ids = payment_lines.mapped('id')
    
                        reconcile_lines = self.env['account.partial.reconcile'].search(
                            ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                        if reconcile_lines:
                            reconcile_lines.unlink()
                        move.mapped('line_ids.analytic_line_ids').unlink()
    
                if rec.mapped('payment_ids'):
                    payment_ids = rec.mapped('payment_ids')
                    payment_ids.mapped('move_line_ids').mapped(
                        'move_id').write({'state': 'draft'})
                    payment_ids.mapped('move_line_ids').mapped('move_id').unlink()
                    payment_ids.mapped(
                        'move_line_ids').write({'state': 'draft'})
                    payment_ids.mapped('move_line_ids').unlink()
    
                    if rec.company_id.payment_operation_type == 'cancel':
                        payment_ids.write({'state': 'cancelled'})
                    elif rec.company_id.payment_operation_type == 'cancel_draft':
                        payment_ids.write(
                            {'state': 'draft', 'move_name': ''})
                    elif rec.company_id.payment_operation_type == 'cancel_delete':
                        payment_ids.write(
                            {'state': 'draft', 'move_name': ''})
                        payment_ids.unlink()
    
                move_line_ids.write({'state': 'draft'})
                move.write({'state': 'draft'})
                rec.move_id = False
                move.unlink()
    
                rec.write(
                    {'state': 'draft', 'move_name': '', 'move_id': False})

    @api.multi
    def action_invoice_cancel_delete(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_account_cancel'):
            raise ValidationError(
                _("Enable Configuration for Account Cancel Feature"))
        else:
            for rec in self:
    
                move = rec.mapped('move_id')
                move_line_ids = move.mapped('line_ids')
                reconcile_ids = []
                if move_line_ids:
                    reconcile_ids = move_line_ids.mapped('id')
                reconcile_lines = self.env['account.partial.reconcile'].search(
                    ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                if reconcile_lines:
                    reconcile_lines.unlink()
    
                if rec.mapped('payment_ids'):
                    payment_ids = rec.mapped('payment_ids')
                    if payment_ids.mapped('move_line_ids'):
                        payment_lines = payment_ids.mapped('move_line_ids')
                        reconcile_ids = payment_lines.mapped('id')
    
                        reconcile_lines = self.env['account.partial.reconcile'].search(
                            ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                        if reconcile_lines:
                            reconcile_lines.unlink()
                        move.mapped('line_ids.analytic_line_ids').unlink()
    
                if rec.mapped('payment_ids'):
                    payment_ids = rec.mapped('payment_ids')
                    payment_ids.mapped('move_line_ids').mapped(
                        'move_id').write({'state': 'draft'})
                    payment_ids.mapped('move_line_ids').mapped('move_id').unlink()
                    payment_ids.mapped(
                        'move_line_ids').write({'state': 'draft'})
                    payment_ids.mapped('move_line_ids').unlink()
    
                    if rec.company_id.payment_operation_type == 'cancel':
                        payment_ids.write({'state': 'cancelled'})
                    elif rec.company_id.payment_operation_type == 'cancel_draft':
                        payment_ids.write(
                            {'state': 'draft', 'move_name': ''})
                    elif rec.company_id.payment_operation_type == 'cancel_delete':
                        payment_ids.write(
                            {'state': 'draft', 'move_name': ''})
                        payment_ids.unlink()
    
                move_line_ids.write({'state': 'draft'})
                move.write({'state': 'draft'})
                rec.move_id = False
                move.unlink()
    
                rec.write(
                    {'state': 'draft', 'move_name': '', 'move_id': False})
                rec.unlink()

    @api.multi
    def sh_cancel(self):

        move = self.mapped('move_id')
        move_line_ids = move.mapped('line_ids')
        reconcile_ids = []
        if move_line_ids:
            reconcile_ids = move_line_ids.mapped('id')
        reconcile_lines = self.env['account.partial.reconcile'].search(
            ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
        if reconcile_lines:
            reconcile_lines.unlink()

        if self.mapped('payment_ids'):
            payment_ids = self.mapped('payment_ids')
            if payment_ids.mapped('move_line_ids'):
                payment_lines = payment_ids.mapped('move_line_ids')
                reconcile_ids = payment_lines.mapped('id')

                reconcile_lines = self.env['account.partial.reconcile'].search(
                    ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                if reconcile_lines:
                    reconcile_lines.unlink()
                move.mapped('line_ids.analytic_line_ids').unlink()

        if self.mapped('payment_ids'):
            payment_ids = self.mapped('payment_ids')
            payment_ids.mapped('move_line_ids').mapped(
                'move_id').write({'state': 'draft'})
            payment_ids.mapped('move_line_ids').mapped('move_id').unlink()
            payment_ids.mapped(
                'move_line_ids').write({'state': 'draft'})
            payment_ids.mapped('move_line_ids').unlink()

            if self.company_id.payment_operation_type == 'cancel':
                payment_ids.write({'state': 'cancelled'})
            elif self.company_id.payment_operation_type == 'cancel_draft':
                payment_ids.write({'state': 'draft', 'move_name': ''})
            elif self.company_id.payment_operation_type == 'cancel_delete':
                payment_ids.write({'state': 'draft', 'move_name': ''})
                payment_ids.unlink()

        move_line_ids.write({'state': 'draft'})
        move.write({'state': 'draft'})
        self.move_id = False
        move.unlink()

        if self.company_id.invoice_operation_type == 'cancel':
            self.write({'state': 'cancel'})
        elif self.company_id.invoice_operation_type == 'cancel_draft':
            self.write(
                {'state': 'draft', 'move_name': '', 'move_id': False})
        elif self.company_id.invoice_operation_type == 'cancel_delete':
            self.write(
                {'state': 'draft', 'move_name': '', 'move_id': False})

        if self.company_id.invoice_operation_type == 'cancel_delete':
            self.unlink()
            return {
                'name': 'Invoices',
                'type': 'ir.actions.act_window',
                'res_model': 'account.invoice',
                'view_type': 'form',
                'view_mode': 'tree,kanban,form',
                'target': 'current',
            }
