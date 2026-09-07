# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, _
from odoo.exceptions import ValidationError


class Expense(models.Model):
    _inherit = 'hr.expense'

    def action_expense_cancel(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_expense_cancel'):
            raise ValidationError(
                _("Enable Configuration for Expense Cancel Feature"))
        else:
            for rec in self:
                rec.write({'state': 'refused'})

    def action_expense_cancel_draft(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_expense_cancel'):
            raise ValidationError(
                _("Enable Configuration for Expense Cancel Feature"))
        else:
            for rec in self:
                rec.write({'state': 'draft'})

    def action_expense_cancel_delete(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_expense_cancel'):
            raise ValidationError(
                _("Enable Configuration for Expense Cancel Feature"))
        else:
            for rec in self:
                rec.write({'state': 'refused'})
                rec.unlink()

    def sh_cancel(self):
        if self.company_id.expense_operation_type == 'cancel':
            self.write({'state': 'refused'})
        elif self.company_id.expense_operation_type == 'cancel_draft':
            self.write({'state': 'draft'})
        elif self.company_id.expense_operation_type == 'cancel_delete':
            self.write({'state': 'refused'})
            self.unlink()
            return {
                'name': 'Expense',
                'type': 'ir.actions.act_window',
                'res_model': 'hr.expense',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'target': 'current',
            }


class ExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    def action_expense_cancel(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_expense_cancel'):
            raise ValidationError(
                _("Enable Configuration for Expense Cancel Feature"))
        else:
            for rec in self:
                if rec.mapped('expense_line_ids'):
                    rec.mapped('expense_line_ids').write(
                        {'state': 'refused'})

                if rec.mapped('account_move_id'):
                    line_ids = rec.mapped('account_move_id').mapped('line_ids')
                    reconcile_ids = line_ids.mapped('id')
                    reconcile_lines = self.env['account.partial.reconcile'].search(
                        ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                    if reconcile_lines:
                        debit_account_move_list = reconcile_lines.mapped(
                            'debit_move_id').mapped('move_id')
                        credit_account_move_list = reconcile_lines.mapped(
                            'credit_move_id').mapped('move_id')
                        reconcile_lines.unlink()

                        for debit_move in debit_account_move_list:
                            debit_move.write({'state': 'draft', 'name': '/'})
                            debit_move.mapped('line_ids').write(
                                {'parent_state': 'draft'})
                            debit_move.mapped('line_ids').unlink()

                        for credit_move in credit_account_move_list:
                            credit_move.write({'state': 'draft', 'name': '/'})
                            credit_move.mapped('line_ids').write(
                                {'parent_state': 'draft'})
                            credit_move.mapped('line_ids').unlink()

                    else:
                        rec.mapped('account_move_id').write(
                            {'state': 'draft', 'name': '/'})
                        rec.mapped('account_move_id').mapped(
                            'line_ids').write({'parent_state': 'draft'})
                        rec.mapped('account_move_id').mapped('line_ids').unlink()

                rec.write({'state': 'cancel'})

    def action_expense_cancel_draft(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_expense_cancel'):
            raise ValidationError(
                _("Enable Configuration for Expense Cancel Feature"))
        else:
            for rec in self:
                if rec.mapped('expense_line_ids'):
                    rec.mapped('expense_line_ids').write(
                        {'state': 'draft'})

                if rec.mapped('account_move_id'):
                    line_ids = rec.mapped('account_move_id').mapped('line_ids')
                    reconcile_ids = line_ids.mapped('id')
                    reconcile_lines = self.env['account.partial.reconcile'].search(
                        ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                    if reconcile_lines:
                        debit_account_move_list = reconcile_lines.mapped(
                            'debit_move_id').mapped('move_id')
                        credit_account_move_list = reconcile_lines.mapped(
                            'credit_move_id').mapped('move_id')
                        reconcile_lines.unlink()

                        for debit_move in debit_account_move_list:
                            debit_move.write({'state': 'draft', 'name': '/'})
                            debit_move.mapped('line_ids').write(
                                {'parent_state': 'draft'})
                            debit_move.mapped('line_ids').unlink()

                        for credit_move in credit_account_move_list:
                            credit_move.write({'state': 'draft', 'name': '/'})
                            credit_move.mapped('line_ids').write(
                                {'parent_state': 'draft'})
                            credit_move.mapped('line_ids').unlink()

                    else:
                        rec.mapped('account_move_id').write(
                            {'state': 'draft', 'name': '/'})
                        rec.mapped('account_move_id').mapped(
                            'line_ids').write({'parent_state': 'draft'})
                        rec.mapped('account_move_id').mapped('line_ids').unlink()

                rec.write({'state': 'draft'})

    def action_expense_cancel_delete(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_expense_cancel'):
            raise ValidationError(
                _("Enable Configuration for Expense Cancel Feature"))
        else:
            for rec in self:
                if rec.mapped('expense_line_ids'):
                    rec.mapped('expense_line_ids').write(
                        {'state': 'refused'})
                    rec.mapped('expense_line_ids').unlink()

                if rec.mapped('account_move_id'):
                    line_ids = rec.mapped('account_move_id').mapped('line_ids')
                    reconcile_ids = line_ids.mapped('id')
                    reconcile_lines = self.env['account.partial.reconcile'].search(
                        ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                    if reconcile_lines:
                        debit_account_move_list = reconcile_lines.mapped(
                            'debit_move_id').mapped('move_id')
                        credit_account_move_list = reconcile_lines.mapped(
                            'credit_move_id').mapped('move_id')
                        reconcile_lines.unlink()

                        for debit_move in debit_account_move_list:
                            debit_move.write({'state': 'draft', 'name': '/'})
                            debit_move.mapped('line_ids').write(
                                {'parent_state': 'draft'})
                            debit_move.mapped('line_ids').unlink()

                        for credit_move in credit_account_move_list:
                            credit_move.write({'state': 'draft', 'name': '/'})
                            credit_move.mapped('line_ids').write(
                                {'parent_state': 'draft'})
                            credit_move.mapped('line_ids').unlink()
                    else:
                        rec.mapped('account_move_id').write(
                            {'state': 'draft', 'name': '/'})
                        rec.mapped('account_move_id').mapped(
                            'line_ids').write({'parent_state': 'draft'})
                        rec.mapped('account_move_id').mapped('line_ids').unlink()

                rec.write({'state': 'cancel'})
                rec.unlink()

    def sh_cancel(self):

        if self.mapped('expense_line_ids'):
            if self.company_id.expense_operation_type == 'cancel':
                self.mapped('expense_line_ids').write(
                    {'state': 'refused'})
            elif self.company_id.expense_operation_type == 'cancel_draft':
                self.mapped('expense_line_ids').write(
                    {'state': 'draft'})
            elif self.company_id.expense_operation_type == 'cancel_delete':
                self.mapped('expense_line_ids').write(
                    {'state': 'refused'})
                self.mapped('expense_line_ids').unlink()

        if self.mapped('account_move_id'):

            line_ids = self.mapped('account_move_id').mapped('line_ids')
            reconcile_ids = line_ids.mapped('id')
            reconcile_lines = self.env['account.partial.reconcile'].search(
                ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
            if reconcile_lines:
                debit_account_move_list = reconcile_lines.mapped(
                    'debit_move_id').mapped('move_id')
                credit_account_move_list = reconcile_lines.mapped(
                    'credit_move_id').mapped('move_id')
                reconcile_lines.unlink()

                for debit_move in debit_account_move_list:
                    debit_move.write({'state': 'draft', 'name': '/'})
                    debit_move.mapped('line_ids').write(
                        {'parent_state': 'draft'})
                    debit_move.mapped('line_ids').unlink()
    #                 debit_move.with_context({'force_delete':True}).unlink()

                for credit_move in credit_account_move_list:
                    credit_move.write({'state': 'draft', 'name': '/'})
                    credit_move.mapped('line_ids').write(
                        {'parent_state': 'draft'})
                    credit_move.mapped('line_ids').unlink()
    #                 credit_move.with_context({'force_delete':True}).unlink()

            else:
                self.mapped('account_move_id').write(
                    {'state': 'draft', 'name': '/'})
                self.mapped('account_move_id').mapped(
                    'line_ids').write({'parent_state': 'draft'})
                self.mapped('account_move_id').mapped('line_ids').unlink()

        if self.company_id.expense_operation_type == 'cancel':
            self.write({'state': 'cancel'})
        elif self.company_id.expense_operation_type == 'cancel_draft':
            self.write({'state': 'draft'})
        elif self.company_id.expense_operation_type == 'cancel_delete':
            self.write({'state': 'cancel'})
            self.unlink()
            return {
                'name': 'Expense Report',
                'type': 'ir.actions.act_window',
                'res_model': 'hr.expense.sheet',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'target': 'current',
            }
