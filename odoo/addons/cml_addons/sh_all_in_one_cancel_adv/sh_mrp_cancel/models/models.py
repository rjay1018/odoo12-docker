# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, _
from odoo.exceptions import ValidationError


class Move(models.Model):
    _inherit = 'stock.move'

    def _sh_unreseve_qty(self):
        for move_line in self.mapped('move_line_ids'):
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


class Production(models.Model):
    _inherit = 'mrp.production'

    def action_mrp_cancel(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_mrp_cancel'):
            raise ValidationError(
                _("Enable Configuration for MRP Cancel Feature"))
        else:
            for rec in self:
                if rec.mapped('move_raw_ids'):
                    rec.mapped('move_raw_ids').write(
                        {'state': 'cancel'})
                    rec.mapped('move_raw_ids').mapped(
                        'move_line_ids').write({'state': 'cancel'})
                    rec.mapped('move_raw_ids')._sh_unreseve_qty()

                if rec.mapped('workorder_ids'):
                    if rec.mapped('workorder_ids').mapped('time_ids'):
                        rec.mapped('workorder_ids').mapped('time_ids').unlink()
                    rec.mapped('workorder_ids').write(
                        {'time_ids': [(6, 0, [])]})
                    workorder_ids = rec.mapped('workorder_ids').ids
                    self.env.cr.execute("""
                        UPDATE mrp_workorder set state='cancel' where id in %s 
                    """, (tuple(workorder_ids),))

                if rec.mapped('move_dest_ids'):
                    rec.mapped('move_dest_ids').write(
                        {'state': 'cancel'})
                    rec.mapped('move_dest_ids').mapped(
                        'move_line_ids').write({'state': 'cancel'})
                    rec.mapped('move_dest_ids')._sh_unreseve_qty()

                if rec.mapped('move_finished_ids'):
                    rec.mapped('move_finished_ids').write(
                        {'state': 'cancel'})
                    rec.mapped('move_finished_ids').mapped(
                        'move_line_ids').write({'state': 'cancel'})
                    rec.mapped('move_finished_ids')._sh_unreseve_qty()

                if rec.mapped('finished_move_line_ids'):
                    rec.mapped('finished_move_line_ids').write(
                        {'state': 'cancel'})

                if rec.mapped('picking_ids'):
                    rec.mapped('picking_ids').mapped(
                        'move_ids_without_package').write({'state': 'cancel'})
                    rec.mapped('picking_ids').mapped('move_ids_without_package').mapped(
                        'move_line_ids').write({'state': 'cancel'})
                    rec.mapped('picking_ids').mapped(
                        'move_ids_without_package')._sh_unreseve_qty()

                    rec.mapped('picking_ids').write({'state': 'cancel'})

                rec.write({'state': 'cancel'})

    def action_mrp_cancel_draft(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_mrp_cancel'):
            raise ValidationError(
                _("Enable Configuration for MRP Cancel Feature"))
        else:
            for rec in self:
                if rec.mapped('move_raw_ids'):
                    rec.mapped('move_raw_ids').write(
                        {'state': 'draft'})
                    rec.mapped('move_raw_ids').mapped(
                        'move_line_ids').write({'state': 'draft'})
                    rec.mapped('move_raw_ids')._sh_unreseve_qty()

                if rec.mapped('workorder_ids'):
                    if rec.mapped('workorder_ids').mapped('time_ids'):
                        rec.mapped('workorder_ids').mapped('time_ids').unlink()
                    rec.mapped('workorder_ids').write(
                        {'time_ids': [(6, 0, [])]})
                    workorder_ids = rec.mapped('workorder_ids').ids
                    self.env.cr.execute("""
                        UPDATE mrp_workorder set state='pending' where id in %s 
                    """, (tuple(workorder_ids),))

                if rec.mapped('move_dest_ids'):
                    rec.mapped('move_dest_ids').write(
                        {'state': 'draft'})
                    rec.mapped('move_dest_ids').mapped(
                        'move_line_ids').write({'state': 'draft'})
                    rec.mapped('move_dest_ids')._sh_unreseve_qty()

                if rec.mapped('move_finished_ids'):
                    rec.mapped('move_finished_ids').write(
                        {'state': 'draft'})
                    rec.mapped('move_finished_ids').mapped(
                        'move_line_ids').write({'state': 'draft'})
                    rec.mapped('move_finished_ids')._sh_unreseve_qty()

                if rec.mapped('finished_move_line_ids'):
                    rec.mapped('finished_move_line_ids').write(
                        {'state': 'draft'})

                if rec.mapped('picking_ids'):
                    rec.mapped('picking_ids').mapped(
                        'move_ids_without_package').write({'state': 'draft'})
                    rec.mapped('picking_ids').mapped('move_ids_without_package').mapped(
                        'move_line_ids').write({'state': 'draft'})
                    rec.mapped('picking_ids').mapped(
                        'move_ids_without_package')._sh_unreseve_qty()
                    rec.mapped('picking_ids').write({'state': 'draft'})

                rec.write({'state': 'confirmed'})

    def action_mrp_cancel_delete(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_mrp_cancel'):
            raise ValidationError(
                _("Enable Configuration for MRP Cancel Feature"))
        else:
            for rec in self:
                if rec.mapped('move_raw_ids'):
                    rec.mapped('move_raw_ids').write(
                        {'state': 'draft'})
                    rec.mapped('move_raw_ids').mapped(
                        'move_line_ids').write({'state': 'draft'})
                    rec.mapped('move_raw_ids')._sh_unreseve_qty()
                    rec.mapped('move_raw_ids').mapped('move_line_ids').unlink()
                    rec.mapped('move_raw_ids').unlink()

                if rec.mapped('workorder_ids'):
                    if rec.mapped('workorder_ids').mapped('time_ids'):
                        rec.mapped('workorder_ids').mapped('time_ids').unlink()
                    rec.mapped('workorder_ids').write(
                        {'time_ids': [(6, 0, [])]})
                    rec.mapped('workorder_ids').unlink()

                if rec.mapped('move_dest_ids'):
                    rec.mapped('move_dest_ids').write(
                        {'state': 'draft'})
                    rec.mapped('move_dest_ids').mapped(
                        'move_line_ids').write({'state': 'draft'})
                    rec.mapped('move_dest_ids')._sh_unreseve_qty()
                    rec.mapped('move_dest_ids').mapped('move_line_ids').unlink()
                    rec.mapped('move_dest_ids').unlink()

                if rec.mapped('move_finished_ids'):
                    rec.mapped('move_finished_ids').write(
                        {'state': 'draft'})
                    rec.mapped('move_finished_ids').mapped(
                        'move_line_ids').write({'state': 'draft'})
                    rec.mapped('move_finished_ids')._sh_unreseve_qty()
                    rec.mapped('move_finished_ids').mapped('move_line_ids').unlink()
                    rec.mapped('move_finished_ids').unlink()

                if rec.mapped('finished_move_line_ids'):
                    rec.mapped('finished_move_line_ids').write(
                        {'state': 'draft'})
                    rec.mapped('finished_move_line_ids').unlink()

                if rec.mapped('picking_ids'):
                    rec.mapped('picking_ids').mapped(
                        'move_ids_without_package').write({'state': 'draft'})
                    rec.mapped('picking_ids').mapped('move_ids_without_package').mapped(
                        'move_line_ids').write({'state': 'draft'})
                    rec.mapped('picking_ids').mapped(
                        'move_ids_without_package')._sh_unreseve_qty()
                    rec.mapped('picking_ids').write({'state': 'draft'})

                rec.write({'state': 'cancel'})

                rec.unlink()

    def sh_cancel(self):

        if self.company_id.mrp_operation_type == 'cancel':
            if self.mapped('move_raw_ids'):
                self.mapped('move_raw_ids').write(
                    {'state': 'cancel'})
                self.mapped('move_raw_ids').mapped(
                    'move_line_ids').write({'state': 'cancel'})
                self.mapped('move_raw_ids')._sh_unreseve_qty()

            if self.mapped('workorder_ids'):
                if self.mapped('workorder_ids').mapped('time_ids'):
                    self.mapped('workorder_ids').mapped('time_ids').unlink()
                self.mapped('workorder_ids').write(
                    {'time_ids': [(6, 0, [])]})
                workorder_ids = self.mapped('workorder_ids').ids
                self.env.cr.execute("""
                    UPDATE mrp_workorder set state='cancel' where id in %s 
                """, (tuple(workorder_ids),))

            if self.mapped('move_dest_ids'):
                self.mapped('move_dest_ids').write(
                    {'state': 'cancel'})
                self.mapped('move_dest_ids').mapped(
                    'move_line_ids').write({'state': 'cancel'})
                self.mapped('move_dest_ids')._sh_unreseve_qty()

            if self.mapped('move_finished_ids'):
                self.mapped('move_finished_ids').write(
                    {'state': 'cancel'})
                self.mapped('move_finished_ids').mapped(
                    'move_line_ids').write({'state': 'cancel'})
                self.mapped('move_finished_ids')._sh_unreseve_qty()

            if self.mapped('finished_move_line_ids'):
                self.mapped('finished_move_line_ids').write(
                    {'state': 'cancel'})

            if self.mapped('picking_ids'):
                self.mapped('picking_ids').mapped(
                    'move_ids_without_package').write({'state': 'cancel'})
                self.mapped('picking_ids').mapped('move_ids_without_package').mapped(
                    'move_line_ids').write({'state': 'cancel'})
                self.mapped('picking_ids').mapped(
                    'move_ids_without_package')._sh_unreseve_qty()

                self.mapped('picking_ids').write({'state': 'cancel'})

            self.write({'state': 'cancel'})
        elif self.company_id.mrp_operation_type == 'cancel_draft':

            if self.mapped('move_raw_ids'):
                self.mapped('move_raw_ids').write(
                    {'state': 'draft'})
                self.mapped('move_raw_ids').mapped(
                    'move_line_ids').write({'state': 'draft'})
                self.mapped('move_raw_ids')._sh_unreseve_qty()

            if self.mapped('workorder_ids'):
                if self.mapped('workorder_ids').mapped('time_ids'):
                    self.mapped('workorder_ids').mapped('time_ids').unlink()
                self.mapped('workorder_ids').write(
                    {'time_ids': [(6, 0, [])]})
                workorder_ids = self.mapped('workorder_ids').ids
                self.env.cr.execute("""
                    UPDATE mrp_workorder set state='pending' where id in %s 
                """, (tuple(workorder_ids),))

            if self.mapped('move_dest_ids'):
                self.mapped('move_dest_ids').write(
                    {'state': 'draft'})
                self.mapped('move_dest_ids').mapped(
                    'move_line_ids').write({'state': 'draft'})
                self.mapped('move_dest_ids')._sh_unreseve_qty()

            if self.mapped('move_finished_ids'):
                self.mapped('move_finished_ids').write(
                    {'state': 'draft'})
                self.mapped('move_finished_ids').mapped(
                    'move_line_ids').write({'state': 'draft'})
                self.mapped('move_finished_ids')._sh_unreseve_qty()

            if self.mapped('finished_move_line_ids'):
                self.mapped('finished_move_line_ids').write(
                    {'state': 'draft'})

            if self.mapped('picking_ids'):
                self.mapped('picking_ids').mapped(
                    'move_ids_without_package').write({'state': 'draft'})
                self.mapped('picking_ids').mapped('move_ids_without_package').mapped(
                    'move_line_ids').write({'state': 'draft'})
                self.mapped('picking_ids').mapped(
                    'move_ids_without_package')._sh_unreseve_qty()
                self.mapped('picking_ids').write({'state': 'draft'})

            self.write({'state': 'confirmed'})
        elif self.company_id.mrp_operation_type == 'cancel_delete':

            if self.mapped('move_raw_ids'):
                self.mapped('move_raw_ids').write(
                    {'state': 'draft'})
                self.mapped('move_raw_ids').mapped(
                    'move_line_ids').write({'state': 'draft'})
                self.mapped('move_raw_ids')._sh_unreseve_qty()
                self.mapped('move_raw_ids').mapped('move_line_ids').unlink()
                self.mapped('move_raw_ids').unlink()

            if self.mapped('workorder_ids'):
                if self.mapped('workorder_ids').mapped('time_ids'):
                    self.mapped('workorder_ids').mapped('time_ids').unlink()
                self.mapped('workorder_ids').write(
                    {'time_ids': [(6, 0, [])]})
                self.mapped('workorder_ids').unlink()

            if self.mapped('move_dest_ids'):
                self.mapped('move_dest_ids').write(
                    {'state': 'draft'})
                self.mapped('move_dest_ids').mapped(
                    'move_line_ids').write({'state': 'draft'})
                self.mapped('move_dest_ids')._sh_unreseve_qty()
                self.mapped('move_dest_ids').mapped('move_line_ids').unlink()
                self.mapped('move_dest_ids').unlink()

            if self.mapped('move_finished_ids'):
                self.mapped('move_finished_ids').write(
                    {'state': 'draft'})
                self.mapped('move_finished_ids').mapped(
                    'move_line_ids').write({'state': 'draft'})
                self.mapped('move_finished_ids')._sh_unreseve_qty()
                self.mapped('move_finished_ids').mapped('move_line_ids').unlink()
                self.mapped('move_finished_ids').unlink()

            if self.mapped('finished_move_line_ids'):
                self.mapped('finished_move_line_ids').write(
                    {'state': 'draft'})
                self.mapped('finished_move_line_ids').unlink()

            if self.mapped('picking_ids'):
                self.mapped('picking_ids').mapped(
                    'move_ids_without_package').write({'state': 'draft'})
                self.mapped('picking_ids').mapped('move_ids_without_package').mapped(
                    'move_line_ids').write({'state': 'draft'})
                self.mapped('picking_ids').mapped(
                    'move_ids_without_package')._sh_unreseve_qty()
                self.mapped('picking_ids').write({'state': 'draft'})

            self.write({'state': 'cancel'})
            self.unlink()
            return {
                'name': 'Manufacturing Orders',
                'type': 'ir.actions.act_window',
                'res_model': 'mrp.production',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'target': 'current',
            }
