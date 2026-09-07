# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from dateutil import relativedelta
from datetime import date, timedelta, datetime


class Consignments(models.Model):
    _name = "stock.consigments"
    _rec_name = "name"
    _order = "name desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Name',
        readonly=True,
        tracking=True,
        copy=False,
    )
    date = fields.Date(
        string='Date',
        readonly=True,
        copy=False,
        default=fields.Date.today()
    )
    start_date = fields.Date(
        string='Start Date',
        required=True,
        copy=False,
        default=datetime.now().strftime('%Y-%m-01'),
    )
    end_date = fields.Date(
        string='To Date',
        required=True,
        copy=False,
        default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
    )
    partner_id = fields.Many2one(
        'res.partner',
        required=True,
        copy=False,
    )
    state = fields.Selection(
        [('draft', 'Draft'),
         ('in_process', 'In Process'),
         ('done', 'Done'),
         ('cancel', 'Cancelled')],
        default='draft',
        string="status",
        tracking=True
    )
    consignments_ids = fields.One2many(
        'stock.consigments.lines',
        'consignments_id',
        string='Consignments',
        copy=False,
    )
    stock_location = fields.Many2one(
        'stock.location',
        string="Stock Location",
        required=True,
        copy=False,
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        readonly=True,
        copy=False,
        default=lambda self: self.env.user.company_id
    )
    user = fields.Many2one(
        'res.users',
        string='User',
        readonly=True,
        copy=False,
        default=lambda self: self.env.user
    )
    note = fields.Text(
        string="Note",
        copy=False,
    )
    # invoice_ids = fields.Many2many(
    #     'account.move',
    #     string='Invoices'
    # )

    acc_invoice_ids = fields.Many2many(
        'account.invoice',
        string='Invoices'
    )

    invoice_count = fields.Integer(
        string="Invoice",
        compute='_invoice_count_compute',
        forece_save=1
    )
    stock_move_count = fields.Integer(
        string="Stock Moves",
        compute='_stock_move_count_compute',
        forece_save=1
    )
    sale_order_count = fields.Integer(
        string="Sale Order",
        compute='_stock_move_count_compute',
        forece_save=1
    )


    @api.onchange('stock_location')
    def _onchange_stock_location(self):
        for rec in self:
            if rec.stock_location.partner_id:
                rec.partner_id = rec.stock_location.partner_id
            else:
                rec.partner_id = None

    def _stock_move_count_compute(self):
        for rec in self:
            rec.update({
                'stock_move_count': len(rec.consignments_ids.mapped('move_ids').ids),
                'sale_order_count': len(rec.consignments_ids.mapped('sale_order_line_ids').mapped('order_id').ids)
            })

    def _invoice_count_compute(self):
        """Compute the number of invoices linked to this consignment.

        Use the record's own many2many to avoid cross-record pollution and
        make the value immediately consistent after invoice creation.
        """
        for rec in self:
            rec.invoice_count = len(rec.acc_invoice_ids)

    def invoice_smart_button(self):
        return {
            'res_model': 'account.invoice',
            'view_mode': 'list,form',
            'name': 'Invoice',
            'domain': [('id', 'in', self.acc_invoice_ids.ids)],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }

    def action_open_stock_move(self):
        action = self.env.ref('stock.stock_move_action').read([])[0]
        action['domain'] = [('id', 'in', self.consignments_ids.mapped('move_ids').ids)]
        return action

    def action_open_sale_order(self):
        action = self.env.ref('sale.action_orders').read([])[0]
        action['domain'] = [('id', 'in', self.consignments_ids.mapped('sale_order_line_ids').mapped('order_id').ids)]
        return action

    @api.multi
    def _get_default_journal(self):
        return self.env['account.journal'].search(
            [('company_id', '=', self.env.user.company_id.id), ('type', '=', 'sale')], limit=1).id

    def _get_sold_pickings(self):
        """Return only the pickings that are actually needed to cover
        ``sold_quantity`` on this consignment.

        We reuse the same FIFO logic as in :meth:`action_done`, but here we
        only *compute* which pickings would be used, without touching stock
        quantities. This keeps the link between invoice and pickings focused on
        the real, sold quantities instead of all potential source moves.
        """
        self.ensure_one()
        Picking = self.env['stock.picking']
        pickings = Picking.browse()

        for line in self.consignments_ids.filtered(lambda l: l.sold_quantity > 0):
            qty_needed = line.sold_quantity
            if qty_needed <= 0:
                continue

            # Same FIFO order as used in action_done: by originating SO date,
            # then SO id, then move date/id.
            def _fifo_key(m):
                so = m.sale_line_id.order_id if m.sale_line_id else False
                if so:
                    dt = so.date_order or so.create_date or m.date
                    return (dt, so.id, m.date, m.id)
                return (m.date, m.id, m.date, m.id)

            moves_fifo = line.move_ids.sorted(key=_fifo_key)

            for move in moves_fifo:
                if qty_needed <= 0:
                    break

                # Remaining qty on this move: same basis as action_confirm,
                # which uses (product_uom_qty - quantity_done) to build lines.
                move_available = move.product_uom_qty - move.quantity_done
                if move_available <= 0:
                    continue

                consume = min(move_available, qty_needed)
                if consume > 0 and move.picking_id not in pickings:
                    pickings |= move.picking_id

                qty_needed -= consume

        return pickings

    def _prepare_consignment_invoice_lines(self, account):
        """Build invoice line commands and SO allocations for this consignment.

        Returns ``(invoice_lines_data, allocations)`` where ``invoice_lines_data``
        is a list of (0, 0, vals) commands for ``invoice_line_ids`` and
        ``allocations`` contains mapping info to later link invoice lines back
        to their originating sale order lines.
        """
        self.ensure_one()

        invoice_lines_data = []
        allocations = []  # keep track of which SO line each invoice line belongs to

        # Total sold quantity on the consignment lines (for consistency checks).
        total_sold_qty = sum(self.consignments_ids.filtered(lambda l: l.sold_quantity > 0).mapped('sold_quantity'))

        # Build invoice lines by allocating each consignment line's sold quantity
        # to its related SO lines (FIFO), capped by qty_delivered-qty_invoiced.
        for con_line in self.consignments_ids.filtered(lambda l: l.sold_quantity > 0):
            qty_remaining = con_line.sold_quantity
            if qty_remaining <= 0:
                continue

            # Candidate SO lines for this product, FIFO by SO date, SO id, SOL id
            sol_product = con_line.sale_order_line_ids.sorted(
                key=lambda sl: (
                    sl.order_id.date_order or sl.order_id.create_date,
                    sl.order_id.id,
                    sl.id,
                )
            )

            for sol in sol_product:
                if qty_remaining <= 0:
                    break

                remaining_to_invoice = max(0.0, sol.qty_delivered - sol.qty_invoiced)
                if remaining_to_invoice <= 0:
                    continue

                allocate = min(remaining_to_invoice, qty_remaining)
                if allocate <= 0:
                    continue

                # Create an invoice line for this specific SO line portion.
                line_vals = {
                    'name': con_line.product_id.display_name,
                    'product_id': con_line.product_id.id,
                    # Explicitly set UoM; ORM won't run onchanges like the UI.
                    'uom_id': con_line.product_uom.id or con_line.product_id.uom_id.id,
                    # NOTE: still using list price; can be refined to use SO pricing rules if required.
                    'price_unit': sol.price_unit,
                    'quantity': allocate,
                    'account_id': account,
                    'discount': sol.discount,
                    'invoice_line_tax_ids': [(6, 0, sol.tax_id.ids)],
                }
                invoice_lines_data.append((0, 0, line_vals))
                allocations.append({
                    'sol_id': sol.id,
                    'product_id': con_line.product_id.id,
                    'discount': sol.discount,
                    'tax_ids': sol.tax_id.ids,
                })

                qty_remaining -= allocate

        # If we managed to build some invoice lines from SO lines, but they do
        # not cover the full sold quantity on the consignment (because SO data
        # is already inconsistent or over-invoiced), treat this consignment as
        # "legacy" as well: drop the SO-based allocation and fall back to a
        # pure consignment-based invoice that does not touch SO qty_invoiced.
        if invoice_lines_data and total_sold_qty:
            so_invoiced_qty = sum(line_vals[2].get('quantity', 0.0) for line_vals in invoice_lines_data)
            if so_invoiced_qty + 1e-6 < total_sold_qty:
                invoice_lines_data = []
                allocations = []

        # Fallback for legacy / inconsistent SO data:
        # If nothing was invoiceable from SO lines but there *is* sold quantity
        # on the consignment, create generic invoice lines directly from the
        # consignment lines, without linking them to sale orders. This avoids
        # touching potentially wrong qty_invoiced on old records.
        if not invoice_lines_data:
            for con_line in self.consignments_ids.filtered(lambda l: l.sold_quantity > 0):
                if con_line.sold_quantity <= 0:
                    continue
                qty_remaining = con_line.sold_quantity
                # Try to distribute the sold qty over related SO lines first,
                # using their discount/tax configuration.
                sol_product = con_line.sale_order_line_ids.sorted(
                    key=lambda sl: (
                        sl.order_id.date_order or sl.order_id.create_date,
                        sl.order_id.id,
                        sl.id,
                    )
                )

                for sol in sol_product:
                    if qty_remaining <= 0:
                        break

                    # In legacy mode we do not trust delivered/invoiced
                    # quantities; just use the SO ordered qty as a soft cap if
                    # it is set, otherwise allocate the remaining qty.
                    so_cap = sol.product_uom_qty or qty_remaining
                    allocate = min(qty_remaining, so_cap) if so_cap > 0 else qty_remaining
                    if allocate <= 0:
                        continue

                    line_vals = {
                        'name': con_line.product_id.display_name,
                        'product_id': con_line.product_id.id,
                        'uom_id': con_line.product_uom.id or con_line.product_id.uom_id.id,
                        'price_unit': sol.price_unit,
                        'quantity': allocate,
                        'account_id': account,
                        'discount': sol.discount,
                        'invoice_line_tax_ids': [(6, 0, sol.tax_id.ids)],
                    }
                    invoice_lines_data.append((0, 0, line_vals))
                    qty_remaining -= allocate

                # Any remaining quantity that cannot be matched to an SO line
                # gets a generic invoice line without SO-specific
                # discount/taxes.
                if qty_remaining > 0:
                    line_vals = {
                        'name': con_line.product_id.display_name,
                        'product_id': con_line.product_id.id,
                        'uom_id': con_line.product_uom.id or con_line.product_id.uom_id.id,
                        'price_unit': con_line.product_id.lst_price,
                        'quantity': qty_remaining,
                        'account_id': account,
                    }
                    invoice_lines_data.append((0, 0, line_vals))

        if not invoice_lines_data:
            # No sold quantity at all
            raise ValidationError(_('There is no sold quantity to invoice on this consignment.'))

        return invoice_lines_data, allocations

    def create_invoice(self):
        """Create customer invoice for sold quantities on this consignment.

        Adds a server-side guard to avoid duplicate invoice creation when the
        button is clicked multiple times or called concurrently.

        Invoice lines are created per (product, sale order line) allocation,
        in FIFO order and capped by each SO line's ``qty_delivered -
        qty_invoiced``. This makes the invoice quantities and the SO
        ``qty_invoiced`` evolution consistent with the consignment FIFO
        delivery logic.
        """
        self.ensure_one()

        # Guard: do not allow creating multiple invoices for the same consignment
        if self.acc_invoice_ids:
            raise ValidationError(_(
                'An invoice has already been created for consignment %s.'
            ) % (self.name,))

        AccountInvoice = self.env['account.invoice']
        journal = self._get_default_journal()
        journal_id = self.env['account.journal'].browse(journal)
        account = journal_id.default_credit_account_id.id

        invoice_lines_data, allocations = self._prepare_consignment_invoice_lines(account)

        move_vals = {
            'date': self.date,
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'type': 'out_invoice',
            'journal_id': journal,
            'reference': self.name,
            'origin': self.name,
            'invoice_line_ids': invoice_lines_data,
            'number': self.name,
        }
        invoice = AccountInvoice.create(move_vals)

        # Link invoice back to this consignment
        self.write({
            'acc_invoice_ids': [(4, invoice.id)],
        })

        # Link only the pickings that are actually needed to cover the sold
        # quantities, using the same FIFO logic as the stock consumption.
        pickings = self._get_sold_pickings()
        if pickings:
            invoice.write({'picking_ids': [(6, 0, pickings.ids)]})

        # Link each created invoice line to its SO line and apply discount/taxes.
        inv_lines = invoice.invoice_line_ids.sorted(key=lambda l: l.id)
        if len(inv_lines) != len(allocations):
            # Fallback: do not try to be clever if something is inconsistent.
            allocations = allocations[:len(inv_lines)]

        for inv_line, alloc in zip(inv_lines, allocations):
            sol = self.env['sale.order.line'].browse(alloc['sol_id'])
            sol.write({'invoice_lines': [(4, inv_line.id)]})
            inv_line.write({
                'discount': alloc['discount'],
                'invoice_line_tax_ids': [(6, 0, alloc['tax_ids'])],
            })

        # Recompute taxes/totals once after all modifications
        invoice._onchange_invoice_line_ids()

        act = self.env.ref('account.action_invoice_tree1').sudo().read([])[0]
        act['domain'] = [('id', 'in', invoice.ids)]
        return act

    def action_recompute_invoice(self):
        """Rebuild linked invoice lines from the current consignment data.

        This is mainly intended for legacy records created before the
        consignment invoicing logic was fixed. It:

        * works only on draft invoices linked in ``acc_invoice_ids``;
        * recomputes invoice lines as if ``create_invoice`` were run now;
        * applies UoM/discount/taxes fixes;
        * keeps ``qty_invoiced`` untouched when the fallback consignment-only
          logic is used (no SO allocations).
        """
        for rec in self:
            if not rec.acc_invoice_ids:
                raise ValidationError(_('There is no invoice linked to this consignment to recompute.'))

            for invoice in rec.acc_invoice_ids:
                if invoice.state != 'draft':
                    raise ValidationError(_(
                        'Invoice %s must be in Draft state to be recomputed from consignment %s.'
                    ) % (invoice.number or invoice.id, rec.name))

                journal = invoice.journal_id
                account = journal.default_credit_account_id.id

                # Clear existing lines first so that qty_invoiced on SO lines is reduced
                # and the calculation sees the correct "remaining" quantity.
                invoice.write({'invoice_line_ids': [(5, 0, 0)]})

                invoice_lines_data, allocations = rec._prepare_consignment_invoice_lines(account)

                # Add the new invoice lines.
                invoice.write({'invoice_line_ids': invoice_lines_data})

                # Link each created invoice line to its SO line and apply
                # discount/taxes where allocations are available. In fallback
                # mode ``allocations`` is empty, so no SO linkage is touched.
                inv_lines = invoice.invoice_line_ids.sorted(key=lambda l: l.id)
                if len(inv_lines) != len(allocations):
                    allocations = allocations[:len(inv_lines)]

                for inv_line, alloc in zip(inv_lines, allocations):
                    sol = rec.env['sale.order.line'].browse(alloc['sol_id'])
                    sol.write({'invoice_lines': [(4, inv_line.id)]})
                    inv_line.write({
                        'discount': alloc['discount'],
                        'invoice_line_tax_ids': [(6, 0, alloc['tax_ids'])],
                    })

                # Recompute invoice taxes/totals once after all modifications
                invoice._onchange_invoice_line_ids()

        return True

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_('You Can not delete this record not in Draft stage'))
            return super(Consignments, self).unlink()

    def action_confirm(self):
        """Populate consignment lines from stock moves based on remaining
        quantities, respecting FIFO by originating sales orders.

        We no longer exclude moves globally (no used_move_ids). Instead we
        rely on each move's remaining quantity (product_uom_qty -
        quantity_done). This allows partially used moves to contribute their
        leftover quantity to future consignments, while FIFO ordering ensures
        that older sales orders (e.g. SO0001) are consumed before newer ones
        (e.g. SO0002).
        """
        for rec in self:
            domain = [
                ('state', '=', 'assigned'),
                ('location_id', '=', rec.stock_location.id),
                # ('partner_id', '=', rec.partner_id.id),
                # ('date', '>=', rec.start_date),
                ('date', '<=', rec.end_date),
                ('company_id', '=', rec.company_id.id),
                # ('sale_line_id', '!=', False),
            ]
            stock_move_ids = rec.env['stock.move'].sudo().search(domain)

            # Sort moves FIFO by sales order date, then SO id, then move date/id
            def _fifo_key(m):
                so = m.sale_line_id.order_id if m.sale_line_id else False
                if so:
                    dt = so.date_order or so.create_date or m.date
                    return (dt, so.id, m.date, m.id)
                return (m.date, m.id, m.date, m.id)

            stock_move_ids = stock_move_ids.sorted(key=_fifo_key)

            product_dict = {}
            for stock_move in stock_move_ids:
                # Remaining quantity on the move only; already done qty has
                # been or will be handled by previous consignments / pickings.
                remaining_qty = stock_move.product_uom_qty - stock_move.quantity_done
                if remaining_qty <= 0:
                    continue

                product = stock_move.product_id
                if product not in product_dict:
                    product_dict[product] = {
                        'quantity': 0,
                        'move_ids': [],
                        'sale_order_line': [],
                    }
                product_dict[product]['quantity'] += remaining_qty
                product_dict[product]['move_ids'].append(stock_move.id)
                if stock_move.sale_line_id:
                    product_dict[product]['sale_order_line'].append(stock_move.sale_line_id.id)

            lines = []
            for product, vals in product_dict.items():
                lines.append((0, 0, {
                    'product_id': product.id,
                    'quantity': vals['quantity'],
                    'product_uom': product.uom_id.id,
                    'move_ids': [(6, 0, vals['move_ids'])],
                    'sale_order_line_ids': [(6, 0, vals['sale_order_line'])]
                }))
            rec.write({
                'consignments_ids': lines,
                'state': 'in_process'
            })

    def action_done(self):
        for rec in self:
            for line in rec.consignments_ids:
                if line.sold_quantity > line.quantity:
                    raise ValidationError(
                        _('You can not transfer more quantity for product: %s then ordered!' %
                          (line.product_id.display_name))
                    )

            picking_to_validate = self.env['stock.picking'].browse()
            for line in rec.consignments_ids.filtered(lambda i: i.sold_quantity > 0):
                quantity = line.sold_quantity

                # Enforce FIFO at consumption time as well: sort moves for this
                # consignment line by originating SO date, then SO id, then
                # move date/id. This ensures that SO0001 is consumed before
                # SO0002 for the same product.
                def _fifo_key(m):
                    so = m.sale_line_id.order_id if m.sale_line_id else False
                    if so:
                        dt = so.date_order or so.create_date or m.date
                        return (dt, so.id, m.date, m.id)
                    return (m.date, m.id, m.date, m.id)

                moves_fifo = line.move_ids.sorted(key=_fifo_key)

                for move in moves_fifo:
                    for ml in move.move_line_ids:
                        if quantity <= 0:
                            break
                        if ml.product_uom_qty > 0:
                            if ml.product_uom_qty >= quantity:
                                ml.qty_done = quantity
                                if move.picking_id not in picking_to_validate:
                                    picking_to_validate += move.picking_id
                                quantity = 0
                                break
                            else:  # ml.product_uom_qty < quantity
                                ml.qty_done = ml.product_uom_qty
                                quantity -= ml.qty_done
                                if move.picking_id not in picking_to_validate:
                                    picking_to_validate += move.picking_id

            for picking in picking_to_validate:
                # ── Package-split guard (SQL-based unpack) ───────────────────
                # When Transfer A used "Put in Pack", Transfer B move lines and
                # the underlying stock.quant records both carry a package_id.
                # Validating multiple move lines that share the same package_id
                # with qty_done > 0 while others have qty_done = 0 triggers:
                #   "You cannot move the same package content more than once
                #    in the same transfer or split the same package."
                #
                # We need to clear package_id from move lines BEFORE
                # button_validate().  However, doing this via ORM write causes
                # Odoo to automatically delete the linked stock.package_level
                # records (visible in logs: "deleted stock.package_level [32]").
                # In v12, stock.package_level.unlink() can call do_unreserve()
                # on the picking, which unreserves ALL products — including
                # items without packaging (e.g. Item 3 from WH/OUT/3333).
                # Because Item 3's reserved_qty may already be partially reduced
                # by an earlier pick in this same loop, do_unreserve overshoots
                # and raises "cannot unreserve more than in stock".
                #
                # Fix: use direct SQL to clear the package fields on move lines
                # and to delete package_level records.  SQL bypasses ALL ORM
                # event hooks, @api.constrains, onchanges, and cascade deletes,
                # giving us the exact DB state we need without side effects.
                # The quant unpack (package_id → NULL on stock.quant) is safe
                # to do via ORM because quant writes have no such cascade.
                packages_in_picking = picking.move_line_ids.mapped('package_id') | picking.move_line_ids.mapped('result_package_id')
                if packages_in_picking:
                    # 1. Unpack quants for products in THIS picking only.
                    #    The product_id filter ensures we don't touch quants for
                    #    products belonging to other pickings that happen to share
                    #    the same physical package.
                    products_in_picking = picking.move_line_ids.mapped('product_id')
                    self.env['stock.quant'].sudo().search([
                        ('package_id', 'in', packages_in_picking.ids),
                        ('location_id', '=', picking.location_id.id),
                        ('product_id', 'in', products_in_picking.ids),
                    ]).write({'package_id': False})

                    # 2. Capture package_level ids BEFORE the SQL wipes the FK.
                    pkg_level_ids = picking.package_level_ids.ids

                    # 3. Clear package refs on move lines via SQL — no ORM cascade.

                    self.env.cr.execute(
                        """
                        UPDATE stock_move_line
                           SET package_id       = NULL,
                               result_package_id = NULL,
                               package_level_id  = NULL
                         WHERE picking_id = %s
                        """,
                        (picking.id,),
                    )

                    # 4. Delete package_level records via SQL — no ORM unlink cascade.
                    if pkg_level_ids:
                        self.env.cr.execute(
                            'DELETE FROM stock_package_level WHERE id IN %s',
                            (tuple(pkg_level_ids),),
                        )

                    # 5. Flush ORM record cache so subsequent reads see the DB state.
                    self.env['stock.move.line'].invalidate_cache(
                        fnames=['package_id', 'result_package_id', 'package_level_id'],
                        ids=picking.move_line_ids.ids,
                    )
                    if pkg_level_ids:
                        self.env['stock.package_level'].invalidate_cache(
                            ids=pkg_level_ids,
                        )
                    self.env['stock.picking'].invalidate_cache(
                        fnames=['package_level_ids'],
                        ids=[picking.id],
                    )
                # ─────────────────────────────────────────────────────────────

                result = picking.with_context(skip_immediate=True, skip_sms=True).button_validate()
                if isinstance(result, dict) and 'context' in result:
                    rec.env['stock.backorder.confirmation'].with_context(
                        result['context'],
                        active_ids=picking.ids,
                        active_model='stock.picking'
                    ).sudo().create({
                        "pick_ids": [(6, 0, [picking.id])],
                    }).process()

                # ── Backorder: fix origin + confirm reservation ───────────────
                # _create_backorder() (called inside button_validate) already
                # calls action_assign() on the new backorder.  We call it once
                # more as a safety net in case the SQL unpack left any state
                # that needs refreshing.  do_unreserve() is intentionally NOT
                # called — see the package-split guard comment above.
                backorder = rec.env['stock.picking'].search([
                    ('backorder_id', '=', picking.id),
                    ('state', 'not in', ['done', 'cancel']),
                ], limit=1)
                if backorder:
                    if not backorder.origin:
                        backorder.write({
                            'origin': picking.origin or picking.name,
                        })
                    backorder.action_assign()
                # ─────────────────────────────────────────────────────────────

            rec.write({'state': 'done'})

    def action_cancel(self):
        for rec in self:
            if rec.state == 'done':
                for con in rec.consignments_ids:
                    for move in con.move_ids:
                        if move.state == 'done':
                            move.action_move_cancel_draft()
                            move._action_confirm()
                            move._action_assign()
                        # Reset quantity_done so these moves can be used again
                        if move.move_line_ids:
                            for ml in move.move_line_ids:
                                ml.qty_done = 0.0
                        else:
                            move.quantity_done = 0.0

                if rec.acc_invoice_ids:
                    for inv in rec.acc_invoice_ids:
                        inv.action_invoice_cancel()

                rec.state = 'cancel'
            elif rec.state in ['draft','in_process']:
                rec.state = 'cancel'


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('stock.consignment')
        return super(Consignments, self).create(vals)


class consignmentsLines(models.Model):
    _name = "stock.consigments.lines"

    product_id = fields.Many2one(
        'product.product',
        string="Product",
        readonly=True
    )
    consignments_id = fields.Many2one(
        'stock.consigments',
    )
    quantity = fields.Float(
        string='Quantity',
        readonly=True
    )
    sold_quantity = fields.Float(
        string='Sold Quantity'
    )
    product_uom = fields.Many2one(
        'uom.uom',
        "Unit of Measure",
        readonly=True
    )
    move_ids = fields.Many2many(
        'stock.move',
        string="Moves",
        readonly=True
    )
    sale_order_line_ids = fields.Many2many(
        'sale.order.line',
        string='Sale Order'
    )
