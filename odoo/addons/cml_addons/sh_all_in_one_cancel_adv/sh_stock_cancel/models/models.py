# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    state = fields.Selection(selection_add=[
        ('cancel', 'Cancel')])
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)

    def action_inventory_scrap_cancel(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_stock_scrap_cancel'):
            raise ValidationError(
                _("Enable Configuration for Scrap Cancel Feature"))
        else:
            for rec in self:
                rec.mapped('move_id').write({'state': 'cancel'})
                rec.mapped('move_id').mapped(
                    'move_line_ids').write({'state': 'cancel'})
                rec._sh_unreseve_qty()
                rec.write({'state': 'cancel'})

    def action_inventory_cancel_scrap_draft(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_stock_scrap_cancel'):
            raise ValidationError(
                _("Enable Configuration for Scrap Cancel Feature"))
        else:
            for rec in self:
                rec.mapped('move_id').write({'state': 'draft'})
                rec.mapped('move_id').mapped(
                    'move_line_ids').write({'state': 'draft'})
                rec._sh_unreseve_qty()
                rec.write({'state': 'draft'})

    def action_inventory_cancel_scrap_delete(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_stock_scrap_cancel'):
            raise ValidationError(
                _("Enable Configuration for Scrap Cancel Feature"))
        else:
            for rec in self:
                rec.mapped('move_id').write({'state': 'draft'})
                rec.mapped('move_id').mapped(
                    'move_line_ids').write({'state': 'draft'})
                rec._sh_unreseve_qty()
                rec.mapped('move_id').unlink()
                rec.mapped('move_id').mapped('move_line_ids').unlink()
                rec.write({'state': 'draft'})
                rec.unlink()

    def _sh_unreseve_qty(self):
        for move_line in self.mapped('move_id').mapped('move_line_ids'):
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
        if self.company_id.scrap_operation_type == 'cancel':

            self.mapped('move_id').write({'state': 'cancel'})
            self.mapped('move_id').mapped(
                'move_line_ids').write({'state': 'cancel'})
            self._sh_unreseve_qty()
            self.write({'state': 'cancel'})

        elif self.company_id.scrap_operation_type == 'cancel_draft':

            self.mapped('move_id').write({'state': 'draft'})
            self.mapped('move_id').mapped(
                'move_line_ids').write({'state': 'draft'})
            self._sh_unreseve_qty()
            self.write({'state': 'draft'})

        elif self.company_id.scrap_operation_type == 'cancel_delete':

            self.mapped('move_id').write({'state': 'draft'})
            self.mapped('move_id').mapped(
                'move_line_ids').write({'state': 'draft'})
            self._sh_unreseve_qty()
            self.mapped('move_id').unlink()
            self.mapped('move_id').mapped('move_line_ids').unlink()
            self.write({'state': 'draft'})
            self.unlink()

            return {
                'name': 'Stock Scrap',
                'type': 'ir.actions.act_window',
                'res_model': 'stock.scrap',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'target': 'current',
            }


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    @api.multi
    def action_inventory_cancel(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_stock_adjustment_cancel'):
            raise ValidationError(
                _("Enable Configuration for Stock Adjustment Cancel Feature"))
        else:
            for rec in self:
                rec.mapped('move_ids').write({'state': 'cancel'})
                rec.mapped('move_ids').mapped(
                    'move_line_ids').write({'state': 'cancel'})
                rec._sh_unreseve_qty()
                rec.write({'state': 'cancel'})

    @api.multi
    def action_inventory_cancel_draft(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_stock_adjustment_cancel'):
            raise ValidationError(
                _("Enable Configuration for Stock Adjustment Cancel Feature"))
        else:
            for rec in self:
                rec.mapped('move_ids').write({'state': 'draft'})
                rec.mapped('move_ids').mapped(
                    'move_line_ids').write({'state': 'draft'})
                rec._sh_unreseve_qty()
                rec.write({'state': 'draft'})

    @api.multi
    def action_inventory_cancel_delete(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_stock_adjustment_cancel'):
            raise ValidationError(
                _("Enable Configuration for Stock Adjustment Cancel Feature"))
        else:
            for rec in self:
                rec.mapped('move_ids').write({'state': 'draft'})
                rec.mapped('move_ids').mapped(
                    'move_line_ids').write({'state': 'draft'})
                rec._sh_unreseve_qty()
                rec.mapped('move_ids').unlink()
                rec.mapped('move_ids').mapped('move_line_ids').unlink()
                rec.write({'state': 'draft'})
                rec.unlink()

    def _sh_unreseve_qty(self):
        for move_line in self.mapped('move_ids').mapped('move_line_ids'):
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
        if self.company_id.adj_operation_type == 'cancel':

            self.mapped('move_ids').write({'state': 'cancel'})
            self.mapped('move_ids').mapped(
                'move_line_ids').write({'state': 'cancel'})
            self._sh_unreseve_qty()
            self.write({'state': 'cancel'})

        elif self.company_id.adj_operation_type == 'cancel_draft':

            self.mapped('move_ids').write({'state': 'draft'})
            self.mapped('move_ids').mapped(
                'move_line_ids').write({'state': 'draft'})
            self._sh_unreseve_qty()
            self.write({'state': 'draft'})

        elif self.company_id.adj_operation_type == 'cancel_delete':

            self.mapped('move_ids').write({'state': 'draft'})
            self.mapped('move_ids').mapped(
                'move_line_ids').write({'state': 'draft'})
            self._sh_unreseve_qty()
            self.mapped('move_ids').unlink()
            self.mapped('move_ids').mapped('move_line_ids').unlink()
            self.write({'state': 'draft'})
            self.unlink()

            return {
                'name': 'Inventory Adjustments',
                'type': 'ir.actions.act_window',
                'res_model': 'stock.inventory',
                'view_type': 'form',
                'view_mode': 'tree,kanban,form',
                'target': 'current',
            }


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
        self._do_unreserve()

    @api.multi
    def action_move_cancel(self):
        if self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_stock_scrap_cancel') == True and self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_stock_cancel') == True and self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_stock_adjustment_cancel') == True:
            for rec in self:
                rec.write({'state': 'cancel'})
                rec.mapped('move_line_ids').write({'state': 'cancel'})
                rec._sh_unreseve_qty()
        else:
            raise ValidationError(
                _("Enable Configuration for Scrap, Transfer, Adjustment  Cancel Feature"))

    @api.multi
    def action_move_cancel_draft(self):
        if self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_stock_scrap_cancel') == True and self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_stock_cancel') == True and self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_stock_adjustment_cancel') == True:
            for rec in self:
                rec.write({'state': 'draft'})
                rec.mapped('move_line_ids').write({'state': 'draft'})
                rec._sh_unreseve_qty()
        else:
            raise ValidationError(
                _("Enable Configuration for Scrap, Transfer, Adjustment  Cancel Feature"))

    @api.multi
    def action_move_cancel_delete(self):
        if self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_stock_scrap_cancel') == True and self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_stock_cancel') == True and self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_stock_adjustment_cancel') == True:
            for rec in self:
                rec.write({'state': 'draft'})
                rec.mapped('move_line_ids').write({'state': 'draft'})
                rec._sh_unreseve_qty()
                rec.mapped('move_line_ids').unlink()
                rec.unlink()
        else:
            raise ValidationError(
                _("Enable Configuration for Scrap, Transfer, Adjustment  Cancel Feature"))


class Picking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_picking_cancel(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_stock_cancel'):
            raise ValidationError(
                _("Enable Configuration for Transfer Cancel Feature"))
        else:
            for rec in self:
                if rec.mapped('move_ids_without_package'):
                    rec.mapped('move_ids_without_package').write(
                        {'state': 'cancel'})
                    rec.mapped('move_ids_without_package').mapped(
                        'move_line_ids').write({'state': 'cancel'})
                    rec._sh_unreseve_qty()
                rec.write({'state': 'cancel'})

    @api.multi
    def action_picking_cancel_draft(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_stock_cancel'):
            raise ValidationError(
                _("Enable Configuration for Transfer Cancel Feature"))
        else:
            for rec in self:
                if rec.mapped('move_ids_without_package'):
                    rec.mapped('move_ids_without_package').write(
                        {'state': 'draft'})
                    rec.mapped('move_ids_without_package').mapped(
                        'move_line_ids').write({'state': 'draft'})
                    rec._sh_unreseve_qty()
                rec.write({'state': 'draft'})

    @api.multi
    def action_picking_cancel_delete(self):
        if not self.env.user.has_group('sh_all_in_one_cancel_adv.group_sh_stock_cancel'):
            raise ValidationError(
                _("Enable Configuration for Transfer Cancel Feature"))
        else:
            for rec in self:
                if rec.mapped('move_ids_without_package'):
                    rec.mapped('move_ids_without_package').write(
                        {'state': 'draft'})
                    rec.mapped('move_ids_without_package').mapped(
                        'move_line_ids').write({'state': 'draft'})
                    rec._sh_unreseve_qty()
                    rec.mapped('move_ids_without_package').mapped(
                        'move_line_ids').unlink()
                    rec.mapped('move_ids_without_package').unlink()
                rec.write({'state': 'draft', 'show_mark_as_todo': True})
                rec.unlink()

    def _sh_unreseve_qty(self):
        self.mapped('move_ids_without_package').write({'state': 'draft'})
        for move_line in self.mapped('move_ids_without_package').mapped('move_line_ids'):
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
            
            move_line.with_context(from_sh_cancel=True).unlink()
        self.mapped('move_ids_without_package').write({'state': 'cancel'})



    @api.multi
    def sh_cancel(self):
        if self.company_id.picking_operation_type == 'cancel':
            print ("356 *************")
            if self.mapped('move_ids_without_package'):
                self.mapped('move_ids_without_package').write(
                    {'state': 'cancel'})

                self.mapped('move_ids_without_package').mapped(
                    'move_line_ids').write({'state': 'cancel'})
                self._sh_unreseve_qty()
#             self.do_unreserve()

            self.write({'state': 'cancel'})

        elif self.company_id.picking_operation_type == 'cancel_draft':
            print ("369 *************")

            if self.mapped('move_ids_without_package'):
                self.mapped('move_ids_without_package').write(
                    {'state': 'draft'})
                self.mapped('move_ids_without_package').mapped(
                    'move_line_ids').write({'state': 'draft'})
                self._sh_unreseve_qty()
#             self.do_unreserve()
            self.write({'state': 'draft'})

        elif self.company_id.picking_operation_type == 'cancel_delete':
            print ("381 *************")

            if self.mapped('move_ids_without_package'):
                self.mapped('move_ids_without_package').write(
                    {'state': 'draft'})
                self.mapped('move_ids_without_package').mapped(
                    'move_line_ids').write({'state': 'draft'})
                self._sh_unreseve_qty()
#                 self.do_unreserve()

                self.mapped('move_ids_without_package').mapped(
                    'move_line_ids').unlink()
                self.mapped('move_ids_without_package').unlink()
            self.write({'state': 'draft', 'show_mark_as_todo': True})
            self.unlink()

            return {
                'name': 'Inventory Transfer',
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_type': 'form',
                'view_mode': 'tree,kanban,form',
                'target': 'current',
            }


class StockQuant(models.Model):
    _inherit = 'stock.quant'




    @api.model
    def _update_reserved_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, strict=False):
        if not self._context.get('from_sh_cancel', False):
            return super(StockQuant, self)._update_reserved_quantity(product_id, location_id, quantity, lot_id, package_id, owner_id, strict)
        
        """ Increase the reserved quantity, i.e. increase `reserved_quantity` for the set of quants
        sharing the combination of `product_id, location_id` if `strict` is set to False or sharing
        the *exact same characteristics* otherwise. Typically, this method is called when reserving
        a move or updating a reserved move line. When reserving a chained move, the strict flag
        should be enabled (to reserve exactly what was brought). When the move is MTS,it could take
        anything from the stock, so we disable the flag. When editing a move line, we naturally
        enable the flag, to reflect the reservation according to the edition.

        :return: a list of tuples (quant, quantity_reserved) showing on which quant the reservation
            was done and how much the system was able to reserve on it
        """
        self = self
        rounding = product_id.uom_id.rounding
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)
        reserved_quants = []

        if float_compare(quantity, 0, precision_rounding=rounding) > 0:
            # if we want to reserve
            available_quantity = sum(quants.filtered(lambda q: float_compare(q.quantity, 0, precision_rounding=rounding) > 0).mapped('quantity')) - sum(quants.mapped('reserved_quantity'))
            if float_compare(quantity, available_quantity, precision_rounding=rounding) > 0:
                raise UserError(_('It is not possible to reserve more products of %s than you have in stock.') % product_id.display_name)
        elif float_compare(quantity, 0, precision_rounding=rounding) < 0:
            # if we want to unreserve
            available_quantity = sum(quants.mapped('reserved_quantity'))
#             if float_compare(abs(quantity), available_quantity, precision_rounding=rounding) > 0:
#                 raise UserError(_('It is not possible to unreserve more products of %s than you have in stock.') % product_id.display_name)
        else:
            return reserved_quants

        for quant in quants:
            if float_compare(quantity, 0, precision_rounding=rounding) > 0:
                max_quantity_on_quant = quant.quantity - quant.reserved_quantity
                if float_compare(max_quantity_on_quant, 0, precision_rounding=rounding) <= 0:
                    continue
                max_quantity_on_quant = min(max_quantity_on_quant, quantity)
                quant.reserved_quantity += max_quantity_on_quant
                reserved_quants.append((quant, max_quantity_on_quant))
                quantity -= max_quantity_on_quant
                available_quantity -= max_quantity_on_quant
            else:
                max_quantity_on_quant = min(quant.reserved_quantity, abs(quantity))
                quant.reserved_quantity -= max_quantity_on_quant
                reserved_quants.append((quant, -max_quantity_on_quant))
                quantity += max_quantity_on_quant
                available_quantity += max_quantity_on_quant

            if float_is_zero(quantity, precision_rounding=rounding) or float_is_zero(available_quantity, precision_rounding=rounding):
                break
        return reserved_quants

