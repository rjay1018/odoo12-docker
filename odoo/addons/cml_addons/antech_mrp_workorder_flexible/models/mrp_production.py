# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    reservation_state = fields.Selection([
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('waiting', 'Waiting Another Operation')],
        string='Material Availability',
        compute='_compute_state', copy=False, index=True, readonly=True,
        store=True, tracking=True,
        help=" * Ready: The material is available to start the production.\n\
                * Waiting: The material is not available to start the production.\n\
                The material availability is impacted by the manufacturing readiness\
                defined on the BoM.")

    def _get_ready_to_produce_state(self):
        """ returns 'assigned' if enough components are reserved in order to complete
        the first operation in the routing. If not returns 'waiting'
        """
        self.ensure_one()
        first_operation = self.routing_id.operation_ids[0]
        # Get BoM line related to first opeation in rounting. If there is only
        # one opeation in the routing then it will need all BoM lines.
        bom_line_ids = self.env['mrp.bom.line']
        if len(self.routing_id.operation_ids) == 1:
            bom_line_ids = self.bom_id.bom_line_ids
        else:
            bom_line_ids = self.bom_id.bom_line_ids.filtered(lambda bl: bl.operation_id == first_operation)
        bom_line_ids = bom_line_ids.filtered(lambda bl: not bl._skip_bom_line(self.product_id))

        moves_in_first_operation = self.move_raw_ids.filtered(lambda m: m.bom_line_id in bom_line_ids)
        if all(move.state == 'assigned' for move in moves_in_first_operation):
            return 'assigned'
        return 'confirmed'

    @api.depends('move_raw_ids.state', 'move_finished_ids.state', 'workorder_ids', 'workorder_ids.state',
                 'qty_produced', 'move_raw_ids.quantity_done', 'product_qty')
    def _compute_state(self):
        """ Compute the production state. It use the same process than stock
        picking. It exists 3 extra steps for production:
        - planned: Workorder has been launched (workorders only)
        - progress: At least one item is produced.
        - to_close: The quantity produced is greater than the quantity to
        produce and all work orders has been finished.
        """
        # TODO: duplicated code with stock_picking.py
        for production in self:
            if production.id:
                if not production.move_raw_ids:
                    # production.state = 'draft'
                    production.state = 'confirmed'
                elif all(move.state == 'draft' for move in production.move_raw_ids):
                    # production.state = 'draft'
                    production.state = 'confirmed'
                elif all(move.state == 'cancel' for move in production.move_raw_ids):
                    production.state = 'cancel'
                elif all(move.state in ['cancel', 'done'] for move in production.move_raw_ids):
                    production.state = 'done'
                elif production.move_finished_ids.filtered(
                        lambda m: m.state not in ('cancel', 'done') and m.product_id.id == production.product_id.id) \
                        and (production.qty_produced >= production.product_qty) \
                        and (not production.routing_id or all(
                    wo_state in ('cancel', 'done') for wo_state in production.workorder_ids.mapped('state'))):
                    # production.state = 'to_close'
                    production.state = 'progress'
                elif production.workorder_ids and any(
                        wo_state in ('progress') for wo_state in production.workorder_ids.mapped('state')) \
                        or production.qty_produced > 0 and production.qty_produced < production.product_uom_qty:
                    production.state = 'progress'
                elif production.workorder_ids:
                    production.state = 'planned'
                else:
                    production.state = 'confirmed'

                # Compute reservation state
                # State where the reservation does not matter.
                if production.state in ('draft', 'done', 'cancel') or not production.move_raw_ids:
                    production.reservation_state = False
                # Compute reservation state according to its component's moves.
                else:
                    relevant_move_state = production.move_raw_ids._get_relevant_state_among_moves()
                    if relevant_move_state == 'partially_available':
                        if production.routing_id and production.routing_id.operation_ids and production.bom_id.ready_to_produce == 'asap':
                            production.reservation_state = production._get_ready_to_produce_state()
                        else:
                            production.reservation_state = 'confirmed'
                    elif relevant_move_state != 'draft':
                        production.reservation_state = relevant_move_state

    def _workorders_create(self, bom, bom_data):
        """
        :param bom: in case of recursive boms: we could create work orders for child
                    BoMs
        """
        workorders = self.env['mrp.workorder']

        # Initial qty producing
        quantity = max(self.product_qty - sum(self.move_finished_ids.filtered(lambda move: move.product_id == self.product_id).mapped('quantity_done')), 0)

        quantity = self.product_id.uom_id._compute_quantity(quantity, self.product_uom_id)
        if self.product_id.tracking == 'serial':
            quantity = 1.0

        for operation in bom.routing_id.operation_ids:
            workorder = workorders.create({
                'name': operation.name,
                'production_id': self.id,
                'workcenter_id': operation.workcenter_id.id,
                'product_uom_id': self.product_id.uom_id.id,
                'operation_id': operation.id,
                'state': len(workorders) == 0 and 'ready' or 'pending',
                'qty_producing': quantity,
                'consumption': self.bom_id.consumption,
            })
            if workorders:
                workorders[-1].next_work_order_id = workorder.id
                workorders[-1]._start_nextworkorder()
            workorders += workorder

            moves_raw = self.move_raw_ids.filtered(lambda move: move.operation_id == operation and move.bom_line_id.bom_id.routing_id == bom.routing_id)
            moves_finished = self.move_finished_ids.filtered(lambda move: move.operation_id == operation)

            # - Raw moves from a BoM where a routing was set but no operation was precised should
            #   be consumed at the last workorder of the linked routing.
            # - Raw moves from a BoM where no rounting was set should be consumed at the last
            #   workorder of the main routing.
            if len(workorders) == len(bom.routing_id.operation_ids):
                moves_raw |= self.move_raw_ids.filtered(lambda move: not move.operation_id and move.bom_line_id.bom_id.routing_id == bom.routing_id)
                moves_raw |= self.move_raw_ids.filtered(lambda move: not move.workorder_id and not move.bom_line_id.bom_id.routing_id)

                moves_finished |= self.move_finished_ids.filtered(lambda move: move.product_id != self.product_id and not move.operation_id)

            moves_raw.mapped('move_line_ids').write({'workorder_id': workorder.id})
            (moves_finished | moves_raw).write({'workorder_id': workorder.id})

            workorder._generate_wo_lines()
        return workorders

    @api.multi
    def action_cancel(self):
        """ Cancels production order, unfinished stock moves and set procurement
        orders in exception """
        if any(workorder.state == 'done' for workorder in self.mapped('workorder_ids')):
            raise UserError(_('You can not cancel production order, a work order is done.'))
        if any(workorder.state == 'progress' for workorder in self.mapped('workorder_ids')):
            for workorder in self.mapped('workorder_ids'):
                workorder.action_cancel()
        return super(MrpProduction, self).action_cancel()
