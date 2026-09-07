# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, _
from odoo.exceptions import ValidationError


class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    def action_landed_cost_cancel(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_stock_landed_cost_cancel'):
            raise ValidationError(
                _("Enable Configuration for Landed Cost Cancel Feature"))
        else:
            for rec in self:
                if rec.mapped('account_move_id'):
                    move = rec.mapped('account_move_id')
                    move_line_ids = move.mapped('line_ids')
                    reconcile_ids = []
                    if move_line_ids:
                        reconcile_ids = move_line_ids.mapped('id')
                    reconcile_lines = self.env['account.partial.reconcile'].search(
                        ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                    if reconcile_lines:
                        reconcile_lines.unlink()
                    move.mapped('line_ids.analytic_line_ids').unlink()
                    move.write({'state': 'draft', 'name': '/'})
                    move.with_context({'force_delete': True}).unlink()

                if rec.mapped('valuation_adjustment_lines'):
                    rec.mapped('valuation_adjustment_lines').unlink()

                rec.write({'state': 'cancel'})

    def action_landed_cost_cancel_draft(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_stock_landed_cost_cancel'):
            raise ValidationError(
                _("Enable Configuration for Landed Cost Cancel Feature"))
        else:
            for rec in self:
                if rec.mapped('account_move_id'):
                    move = rec.mapped('account_move_id')
                    move_line_ids = move.mapped('line_ids')
                    reconcile_ids = []
                    if move_line_ids:
                        reconcile_ids = move_line_ids.mapped('id')
                    reconcile_lines = self.env['account.partial.reconcile'].search(
                        ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                    if reconcile_lines:
                        reconcile_lines.unlink()
                    move.mapped('line_ids.analytic_line_ids').unlink()
                    move.write({'state': 'draft', 'name': '/'})
                    move.with_context({'force_delete': True}).unlink()

                if rec.mapped('valuation_adjustment_lines'):
                    rec.mapped('valuation_adjustment_lines').unlink()

                rec.write({'state': 'draft'})

    def action_landed_cost_cancel_delete(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_stock_landed_cost_cancel'):
            raise ValidationError(
                _("Enable Configuration for Landed Cost Cancel Feature"))
        else:
            for rec in self:
                if rec.mapped('account_move_id'):
                    move = rec.mapped('account_move_id')
                    move_line_ids = move.mapped('line_ids')
                    reconcile_ids = []
                    if move_line_ids:
                        reconcile_ids = move_line_ids.mapped('id')
                    reconcile_lines = self.env['account.partial.reconcile'].search(
                        ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
                    if reconcile_lines:
                        reconcile_lines.unlink()
                    move.mapped('line_ids.analytic_line_ids').unlink()
                    move.write({'state': 'draft', 'name': '/'})
                    move.with_context({'force_delete': True}).unlink()

                if rec.mapped('valuation_adjustment_lines'):
                    rec.mapped('valuation_adjustment_lines').unlink()

                rec.write({'state': 'cancel'})

            for rec in self:
                rec.unlink()

    def sh_cancel(self):

        if self.mapped('account_move_id'):

            move = self.mapped('account_move_id')
            move_line_ids = move.mapped('line_ids')
            reconcile_ids = []
            if move_line_ids:
                reconcile_ids = move_line_ids.mapped('id')
            reconcile_lines = self.env['account.partial.reconcile'].search(
                ['|', ('credit_move_id', 'in', reconcile_ids), ('debit_move_id', 'in', reconcile_ids)])
            if reconcile_lines:
                reconcile_lines.unlink()

            move.mapped('line_ids.analytic_line_ids').unlink()
            move.write({'state': 'draft', 'name': '/'})
            move.with_context({'force_delete': True}).unlink()

        if self.mapped('valuation_adjustment_lines'):
            self.mapped('valuation_adjustment_lines').unlink()

        if self.company_id.landed_cost_operation_type == 'cancel':
            self.write({'state': 'cancel'})
        elif self.company_id.landed_cost_operation_type == 'cancel_draft':
            self.write({'state': 'draft'})
        elif self.company_id.landed_cost_operation_type == 'cancel_delete':
            self.write({'state': 'cancel'})
            self.unlink()

            return {
                'name': 'Landed Costs',
                'type': 'ir.actions.act_window',
                'res_model': 'stock.landed.cost',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'target': 'current',
            }
