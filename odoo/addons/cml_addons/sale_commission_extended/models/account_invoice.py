from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    COMP = [
        ('partner_categ', 'Partner Category Only'),
        ('product_categ', 'Product Category Only'),
        ('both', 'Both Partner and Product')
    ]

    agent_id = fields.Many2one('res.partner', 'Sales Agent')
    computation = fields.Selection(COMP, default='both')
    commission_total = fields.Float(
        string='Commission Total',
        compute='_compute_commission_total',
        store=True,
    )

    @api.depends('invoice_line_ids.agents.amount', 'invoice_line_ids.product_categ_comm_ids.amount')
    def _compute_commission_total(self):
        for obj in self:
            total = 0.0
            for l in obj.invoice_line_ids:
                total += sum(x.amount for x in l.agents)
                total += sum(x.amount for x in l.product_categ_comm_ids)
            obj.commission_total = total

    @api.onchange('partner_id')
    def onchange_partner(self):
        self.agent_id = None
        agent_ids = []
        domain = [('agent', '!=', False)]
        if self.partner_id:
            for p in self.partner_id.partner_categ_comm_ids:
                if p.agent_id.id not in agent_ids:
                    agent_ids.append(p.agent_id.id)
            for p in self.partner_id.product_categ_comm_ids:
                if p.agent_id.id not in agent_ids:
                    agent_ids.append(p.agent_id.id)

        if agent_ids:
            domain.extend([('id', 'in', agent_ids)])
        return {'domain': {'agent_id': domain}}

    @api.onchange('agent_id', 'computation')
    def onchange_agent_id(self):
        """When accounting sets/changes agent_id on the invoice,
        force-recompute all commission lines on the invoice lines."""
        for line in self.invoice_line_ids:
            line._compute_partner_categ_commission()
            line._compute_product_categ_commission()

    @api.multi
    def action_invoice_cancel(self):
        """Clear commission lines when invoice is cancelled.
        Prevents cancelled invoices from appearing in future settlements.
        Only unsettled commission lines are cleared — settled ones are kept
        for audit trail.
        """
        AgentLine = self.env['account.invoice.line.agent']
        CategLine = self.env['account.invoice.line.categ']
        for inv in self:
            line_ids = inv.invoice_line_ids.ids
            # Only remove unsettled commission lines
            AgentLine.search([
                ('object_id', 'in', line_ids),
                ('settled', '=', False),
            ]).unlink()
            CategLine.search([
                ('object_id', 'in', line_ids),
                ('settled', '=', False),
            ]).unlink()
        return super(AccountInvoice, self).action_invoice_cancel()

    @api.multi
    def action_recompute_commissions(self):
        """Force-recompute commission lines by directly writing child records.
        Bypasses stored computed field machinery (which is unreliable for O2M).
        Requires agent_id to be set first.
        """
        for inv in self:
            if not inv.agent_id:
                raise UserError(
                    _("Please set a Sales Agent on the invoice before recomputing commissions.")
                )

        AgentLine = self.env['account.invoice.line.agent']
        CategLine = self.env['account.invoice.line.categ']

        for inv in self:

            _logger.info(
                "SCE recompute: invoice=%s agent=%s computation=%s partner=%s",
                inv.name, inv.agent_id.name, inv.computation, inv.partner_id.name
            )
            lines = inv.invoice_line_ids.filtered(
                lambda l: not getattr(l, 'display_type', False)
                or l.display_type not in ('line_note', 'line_section')
            )
            for line in lines:
                # Auto-fix categ_id from product if missing
                if not line.categ_id and line.product_id:
                    line.categ_id = line.product_id.categ_id

                subtotal = line.price_subtotal
                if line.product_id and line.product_id.standard_price:
                    net = max(0, subtotal - line.product_id.standard_price * line.quantity)
                else:
                    net = subtotal

                # --- Partner Category Commissions ---
                agent_lines = AgentLine.search([('object_id', '=', line.id)])
                required_agents_comms = []
                if inv.computation != 'product_categ':
                    agents_comms = inv.partner_id.partner_categ_comm_ids.filtered(
                        lambda c: c.agent_id.id == inv.agent_id.id
                    )
                    _logger.info(
                        "SCE line %s (product=%s categ=%s): %s partner_categ comm(s) found",
                        line.id, line.product_id.name, line.categ_id.name, len(agents_comms)
                    )
                    for a in agents_comms:
                        base = net if a.commission_id.amount_base_type == 'net_amount' else subtotal
                        amount = self._sce_calc_amount(a.commission_id, base, line.quantity)
                        if amount is not None:
                            required_agents_comms.append({
                                'agent': a.agent_id.id,
                                'commission': a.commission_id.id,
                                'amount': amount,
                            })

                for ex in agent_lines:
                    match = next((r for r in required_agents_comms if r['agent'] == ex.agent.id and r['commission'] == ex.commission.id), None)
                    if match:
                        ex.amount = match['amount']
                        required_agents_comms.remove(match)
                        _logger.info("SCE   -> Updated agent=%s commission=%s amount=%s", ex.agent.name, ex.commission.name, ex.amount)
                # Create remaining
                for r in required_agents_comms:
                    _logger.info("SCE   -> Created agent=%s commission=%s amount=%s", r['agent'], r['commission'], r['amount'])
                    AgentLine.create({
                        'object_id': line.id,
                        'agent': r['agent'],
                        'commission': r['commission'],
                        'amount': r['amount'],
                    })

                # --- Product Category Commissions ---
                categ_lines = CategLine.search([('object_id', '=', line.id)])
                required_prod_comms = []
                if inv.computation != 'partner_categ' and line.categ_id:
                    prod_comms = inv.partner_id.product_categ_comm_ids.filtered(
                        lambda c: c.categ_id.id == line.categ_id.id
                        and c.agent_id.id == inv.agent_id.id
                    )
                    _logger.info(
                        "SCE line %s: %s product_categ comm(s) found",
                        line.id, len(prod_comms)
                    )
                    for a in prod_comms:
                        uom_ok = not a.commission_id.uom_ids or \
                            a.commission_id.uom_ids.filtered(lambda u: u.id == line.uom_id.id)
                        if uom_ok:
                            base = net if a.commission_id.amount_base_type == 'net_amount' else subtotal
                            amount = self._sce_calc_amount(a.commission_id, base, line.quantity)
                            required_prod_comms.append({
                                'categ_id': line.categ_id.id,
                                'qty': line.quantity,
                                'agent': a.agent_id.id,
                                'commission': a.commission_id.id,
                                'amount': amount,
                            })

                # Sync CategLine
                for ex in categ_lines:
                    match = next((r for r in required_prod_comms if r['agent'] == ex.agent.id and r['commission'] == ex.commission.id), None)
                    if match:
                        ex.amount = match['amount']
                        ex.qty = match['qty']
                        ex.categ_id = match['categ_id']
                        required_prod_comms.remove(match)
                        _logger.info("SCE   -> Updated categ agent=%s commission=%s amount=%s", ex.agent.name, ex.commission.name, ex.amount)

                # Create remaining
                for r in required_prod_comms:
                    _logger.info("SCE   -> Created categ agent=%s commission=%s amount=%s", r['agent'], r['commission'], r['amount'])
                    CategLine.create({
                        'object_id': line.id,
                        'categ_id': r['categ_id'],
                        'qty': r['qty'],
                        'agent': r['agent'],
                        'commission': r['commission'],
                        'amount': r['amount'],
                    })
        return True

    @api.model
    def _sce_calc_amount(self, commission, subtotal, quantity):
        """Calculate commission amount given a commission record and base values."""
        _logger.info("SCE CALC -> Commission '%s' Type: '%s', Base: %s, Qty: %s", commission.name, commission.commission_type, subtotal, quantity)
        if commission.commission_type == 'fix':
            amt = quantity * commission.fix_qty
            _logger.info("SCE CALC -> FIX: %s * %s = %s", quantity, commission.fix_qty, amt)
            return amt
        elif commission.commission_type == 'pct':
            amt = subtotal * (commission.fix_qty / 100.0)
            _logger.info("SCE CALC -> PCT: %s * (%s / 100.0) = %s", subtotal, commission.fix_qty, amt)
            return amt
        elif commission.commission_type == 'section':
            _logger.info("SCE CALC -> SECTION logic evaluating...")
            for s in commission.sections:
                if s.amount_from <= subtotal <= s.amount_to:
                    amt = subtotal * (s.percent / 100.0)
                    _logger.info("SCE CALC -> MATCHED SECTION %s-%s: %s * (%s / 100.0) = %s", s.amount_from, s.amount_to, subtotal, s.percent, amt)
                    return amt
            _logger.info("SCE CALC -> NO SECTIONS MATCHED. Returning 0.0")
            return 0.0
        
        _logger.info("SCE CALC -> UNKNOWN COMMISSION TYPE: '%s'. Returning None", commission.commission_type)
        return None

    def recompute_lines_agents(self):
        """Override OCA base method — redirect to action_recompute_commissions."""
        self.action_recompute_commissions()


class AccountInvoiceLine(models.Model):
    _inherit = [
        "account.invoice.line",
        "sale.commission.mixin",
    ]
    _name = "account.invoice.line"

    categ_id = fields.Many2one('product.category', 'Category')
    # product_categ_comm_ids = fields.One2many('account.invoice.line.categ', 'object_id', compute='_compute_categ_commission', store=True)
    agents = fields.One2many(string="Agents & commissions", comodel_name="account.invoice.line.agent", compute='_compute_partner_categ_commission', store=True)
    product_categ_comm_ids = fields.One2many('account.invoice.line.categ', 'object_id', compute='_compute_product_categ_commission', store=True)

    @api.model
    def create(self, vals):
        """Add agents for records created from automations instead of UI."""
        # We use this form as this is the way it's returned when no real vals
        agents_vals = vals.get('agents', [(6, 0, [])])
        invoice_id = vals.get('invoice_id', False)
        if (agents_vals and agents_vals[0][0] == 6 and not
                agents_vals[0][2] and invoice_id):
            vals['agents'] = self._prepare_agents_vals(vals=vals)
        res = super().create(vals)

        # Collect invoice-level updates to write ONCE per invoice.
        # Writing agent_id inside the per-line loop would trigger
        # @api.depends('invoice_id.agent_id') for every line already
        # created, causing an O(N²) cascade of DELETE/INSERT on agent records.
        inv_updates = {}  # {invoice_id: {agent_id, computation}}
        for r in res:
            for sol in r.sale_line_ids:
                if not r.categ_id:
                    r.categ_id = sol.categ_id.id
                inv = r.invoice_id
                if inv.id not in inv_updates and sol.order_id.agent_id:
                    inv_updates[inv.id] = {
                        'agent_id': sol.order_id.agent_id.id,
                        'computation': sol.order_id.computation,
                    }

        # Write agent_id once per invoice (only if invoice has no agent yet)
        for inv_id, update_vals in inv_updates.items():
            inv = self.env['account.invoice'].browse(inv_id)
            if not inv.agent_id:
                inv.write(update_vals)
        return res

    @api.onchange('product_id')
    def onchange_product(self):
        # Note: base @api.onchange('product_id') is called automatically by Odoo MRO.
        # We only need to sync categ_id from the selected product.
        if self.product_id:
            if self.product_id.categ_id.id != self.categ_id.id:
                self.categ_id = self.product_id.categ_id.id

    @api.onchange('categ_id')
    def onchange_category(self):
        domain = []
        if self.categ_id:
            domain =[('categ_id', '=', self.categ_id.id)]
        return {'domain': {'product_id': domain}}

    @api.multi
    @api.depends('categ_id', 'quantity', 'invoice_id.agent_id', 'invoice_id.computation')
    def _compute_partner_categ_commission(self):
        for obj in self:
            if obj.invoice_id.computation != 'product_categ':
                obj._get_agents_comms_per_category('partner')
            else:
                obj.agents = [(5, 0, 0)]

    @api.multi
    @api.depends('categ_id', 'quantity', 'uom_id', 'invoice_id.agent_id', 'invoice_id.computation')
    def _compute_product_categ_commission(self):
        for obj in self:
            if obj.invoice_id.computation != 'partner_categ':
                obj._get_agents_comms_per_category('product')
            else:
                obj.product_categ_comm_ids = [(5, 0, 0)]

    @api.multi
    def _get_agent_comms(self, categ=''):
        agents_comms = None
        if categ == 'partner':
            # Do NOT write self.agents here — it causes extra DELETE inside
            # a compute method and triggers cascades. Clearing is done via
            # (5,0,0) in _get_agents_comms_per_category.
            agents_comms = self.invoice_id.partner_id.partner_categ_comm_ids
            if self.invoice_id.agent_id:
                agents_comms = agents_comms.filtered(lambda c: c.agent_id.id == self.invoice_id.agent_id.id)
        else:
            agents_comms = self.invoice_id.partner_id.product_categ_comm_ids.filtered(lambda c: c.categ_id.id == self.categ_id.id)
            if self.invoice_id.agent_id:
                agents_comms = agents_comms.filtered(lambda c: c.agent_id.id == self.invoice_id.agent_id.id)
        return agents_comms

    @api.multi
    def _get_agents_comms_per_category(self, categ=''):
        for obj in self:
            if getattr(obj, 'display_type', False) in ('line_note', 'line_section'):
                continue
            agents_comms = obj._get_agent_comms(categ)
            
            new_lines = [(5, 0, 0)]  # Start by clearing existing lines
            
            if agents_comms:
                for a in agents_comms:
                    amount = 0
                    subtotal = obj.price_subtotal

                    if a.commission_id.amount_base_type == 'net_amount':
                        subtotal = max([0, obj.price_subtotal - obj.product_id.standard_price * obj.quantity])

                    if a.commission_id.commission_type == 'fix':
                        amount = obj.quantity * a.commission_id.fix_qty
                    elif a.commission_id.commission_type == 'pct':
                        amount = subtotal * (a.commission_id.fix_qty / 100.0)
                    else:
                        for s in a.commission_id.sections:
                            if s.amount_from <= subtotal <= s.amount_to:
                                amount = subtotal * (s.percent / 100.0)

                    vals = {
                        'agent': a.agent_id.id,
                        'commission': a.commission_id.id,
                        'amount': amount
                    }
                    
                    if categ == 'partner':
                        new_lines.append((0, 0, vals))
                    else:
                        vals['categ_id'] = obj.categ_id.id
                        vals['qty'] = obj.quantity

                        # Check if UOM has commission
                        if a.commission_id.uom_ids.filtered(lambda u: u.id == obj.uom_id.id):
                            new_lines.append((0, 0, vals))

            if categ == 'partner':
                obj.agents = new_lines
            else:
                obj.product_categ_comm_ids = new_lines

    # @api.depends('categ_id', 'quantity')
    # def _compute_categ_commission(self):
    #     self._get_agents_comm_per_category()

    # @api.multi
    # def _get_agents_comm_per_category(self):
    #     for obj in self:
    #         obj.product_categ_comm_ids = None
    #         agents_comms = obj.invoice_id.partner_id.product_categ_comm_ids.filtered(lambda c: c.categ_id.id == obj.categ_id.id)
    #         for a in agents_comms:
    #             amount = 0
    #             subtotal = obj.price_subtotal

    #             if a.commission_id.amount_base_type == 'net_amount':
    #                 subtotal = max([0, obj.price_subtotal - obj.product_id.standard_price * obj.quantity])

    #             if a.commission_id.commission_type == 'fix':
    #                 amount = obj.quantity * a.commission_id.fix_qty
    #             elif a.commission_id.commission_type == 'pct':
    #                 amount = subtotal * (a.commission_id.fix_qty / 100.0)
    #             else:
    #                 for s in a.commission_id.sections:
    #                     if s.amount_from <= subtotal <= s.amount_to:
    #                         amount = subtotal * (s.percent / 100.0)

    #             vals = {
    #                 # 'object_id': obj.id,
    #                 'categ_id': obj.categ_id.id,
    #                 'qty': obj.quantity,
    #                 'agent': a.agent_id.id,
    #                 'commission': a.commission_id.id,
    #                 'amount': amount
    #             }
    #             obj.product_categ_comm_ids = [(0, 0, vals)]


class AccountInvoiceLineCateg(models.Model):
    _inherit = "sale.commission.line.mixin"
    _name = "account.invoice.line.categ"

    object_id = fields.Many2one(
        comodel_name="account.invoice.line",
        oldname='invoice_line',
    )
    invoice = fields.Many2one(
        string="Invoice",
        comodel_name="account.invoice",
        related="object_id.invoice_id",
        store=True,
    )
    invoice_date = fields.Date(
        string="Invoice date",
        related="invoice.date_invoice",
        store=True,
        readonly=True,
    )
    # agent_line = fields.Many2many(
    #     comodel_name='sale.commission.settlement.line',
    #     relation='settlement_agent_line_categ_rel',
    #     column1='agent_line_id',
    #     column2='settlement_id',
    #     copy=False,
    # )
    agent_line_categ = fields.Many2many(
        comodel_name='sale.commission.settlement.line.categ',
        relation='settlement_agent_line_categ_rel',
        column1='agent_line_categ_id',
        column2='settlement_id',
        copy=False,
    )
    settled = fields.Boolean(
        compute="_compute_settled",
        store=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        compute="_compute_company",
        store=True,
    )
    currency_id = fields.Many2one(
        related="object_id.currency_id",
        readonly=True,
    )

    @api.depends('object_id.price_subtotal')
    def _compute_amount(self):
        for line in self:
            inv_line = line.object_id
            line.amount = line._get_commission_amount(
                line.commission, inv_line.price_subtotal,
                inv_line.product_id, inv_line.quantity,
            )
            # Refunds commissions are negative
            if 'refund' in line.invoice.type:
                line.amount = -line.amount

    @api.depends('agent_line_categ', 'agent_line_categ.settlement.state', 'invoice', 'invoice.state')
    def _compute_settled(self):
        # Count lines of not open or paid invoices as settled for not
        # being included in settlements
        for line in self:
            line.settled = (any(x.settlement.state != 'cancel' for x in line.agent_line_categ))

    @api.depends('object_id', 'object_id.company_id')
    def _compute_company(self):
        for line in self:
            line.company_id = line.object_id.company_id

    @api.constrains('agent', 'amount')
    def _check_settle_integrity(self):
        # Overridden to allow flexible amount updates even if settled
        pass

    @api.multi
    def unlink(self):
        # Find related settlement lines before we delete
        settlement_lines = self.env['sale.commission.settlement.line.categ'].search([('agent_line_categ', 'in', self.ids)])
        
        # Bypass any constraint by setting settled to False
        self.write({'settled': False})
        res = super(AccountInvoiceLineCateg, self).unlink()
        
        # Cleanup any settlement lines that are now empty (blank lines)
        for sl in settlement_lines:
            if sl.exists() and not sl.agent_line_categ:
                sl.unlink()
                
        return res

    def _skip_settlement(self):
        """This function should return if the commission can be payed.

        :return: bool
        """
        self.ensure_one()
        return (
            self.commission.invoice_state == 'paid' and
            self.invoice.state != 'paid'
        ) or (self.invoice.state not in ('open', 'paid'))

class AccountInvoiceLineAgent(models.Model):
    _inherit = "account.invoice.line.agent"

    @api.constrains('agent', 'amount')
    def _check_settle_integrity(self):
        # Overridden to allow flexible amount updates even if settled
        pass

    @api.multi
    def unlink(self):
        # Find related settlement lines before we delete
        settlement_lines = self.env['sale.commission.settlement.line'].search([('agent_line', 'in', self.ids)])
        
        # Bypass any constraint by setting settled to False
        self.write({'settled': False})
        res = super(AccountInvoiceLineAgent, self).unlink()
        
        # Cleanup any settlement lines that are now empty (blank lines)
        for sl in settlement_lines:
            if sl.exists() and not sl.agent_line:
                sl.unlink()
                
        return res
