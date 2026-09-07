from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class SaleCommissionMakeSettle(models.TransientModel):
    _inherit = "sale.commission.make.settle"

    def _get_unsettled_invoices(self, inv_for, date_to_agent, agent_id):
        args = [
                ('invoice_date', '<', date_to_agent),
                ('agent', '=', agent_id),
                ('settled', '=', False),
                # Exclude commission lines from cancelled invoices
                ('object_id.invoice_id.state', '!=', 'cancel'),
            ]
        if inv_for == 'partner_categ':
            return self.env['account.invoice.line.agent'].search(args, order='invoice_date')
        else:
            return self.env['account.invoice.line.categ'].search(args, order='invoice_date')

    def _process_settlement(self, agent, agent_lines, inv_for):
        settlement_obj = self.env['sale.commission.settlement']
        settlement_line_obj = self.env['sale.commission.settlement.line']
        settlement_line_categ_obj = self.env['sale.commission.settlement.line.categ']
        settlement_ids = []

        for company in agent_lines.mapped('company_id'):
            agent_lines_company = agent_lines.filtered(lambda r: r.object_id.company_id == company)
            if not agent_lines_company:
                continue
            pos = 0
            sett_to = date(year=1900, month=1, day=1)
            while pos < len(agent_lines_company):
                line = agent_lines_company[pos]
                pos += 1
                if line._skip_settlement():
                    continue
                if line.invoice_date > sett_to:
                    sett_from = self._get_period_start(agent, line.invoice_date)
                    sett_to = self._get_next_period_date(agent, sett_from) - timedelta(days=1)
                    settlement = self._get_settlement(agent, company, sett_from, sett_to)
                    if not settlement:
                        settlement = settlement_obj.create(
                                self._prepare_settlement_vals(
                                    agent, company, sett_from, sett_to
                            )
                        )
                    settlement_ids.append(settlement.id)

                vals = {'settlement': settlement.id}
                if inv_for == 'partner_categ':
                    vals['agent_line'] = [(6, 0, [line.id])]
                    settlement_line_obj.create(vals)
                else:
                    vals['agent_line_categ'] = [(6, 0, [line.id])]
                    settlement_line_categ_obj.create(vals)
        return settlement_ids

    @api.multi
    def action_settle(self):
        self.ensure_one()
        settlement_ids = []
        if not self.agents:
            self.agents = self.env['res.partner'].search([('agent', '=', True)])
        date_to = self.date_to
        for agent in self.agents:
            date_to_agent = self._get_period_start(agent, date_to)

            # Partner Category
            settlement_ids.extend(self._process_settlement(
                        agent,
                        self._get_unsettled_invoices('partner_categ', date_to_agent, agent.id),
                        'partner_categ'
                    )
                )

            # Product Category
            settlement_ids.extend(self._process_settlement(
                        agent,
                        self._get_unsettled_invoices('product_categ', date_to_agent, agent.id),
                        'product_categ'
                    )
                )

        if len(settlement_ids):
            return {
                'name': _('Created Settlements'),
                'type': 'ir.actions.act_window',
                'views': [[False, 'list'], [False, 'form']],
                'res_model': 'sale.commission.settlement',
                'domain': [['id', 'in', settlement_ids]],
            }
        else: return {'type': 'ir.actions.act_window_close'}



class Settlement(models.Model):
    _inherit = "sale.commission.settlement"

    categ_lines = fields.One2many(comodel_name="sale.commission.settlement.line.categ", inverse_name="settlement", readonly=True)

    @api.depends('lines', 'lines.settled_amount', 'categ_lines', 'categ_lines.settled_amount')
    def _compute_total(self):
        for record in self:
            record.total = sum(x.settled_amount for x in record.lines) + sum(x.settled_amount for x in record.categ_lines)

    @api.multi
    def action_export_excel(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/sale_commission_extended/export_excel/%s' % self.id,
            'target': 'self',
        }

    @api.multi
    def action_cancel(self):
        """Override to reset settled=False on both commission line types.
        OCA base resets account.invoice.line.agent but NOT our custom
        account.invoice.line.categ lines — they get stuck as settled=True.
        """
        for settlement in self:
            # Reset partner category commission lines (account.invoice.line.agent)
            agent_lines = settlement.lines.mapped('agent_line')
            agent_lines.write({'settled': False})
            # Reset product category commission lines (account.invoice.line.categ)
            categ_lines = settlement.categ_lines.mapped('agent_line_categ')
            categ_lines.write({'settled': False})
        return super(Settlement, self).action_cancel()



class SettlementLineCateg(models.Model):
    _name = "sale.commission.settlement.line.categ"

    settlement = fields.Many2one("sale.commission.settlement", readonly=True, ondelete="cascade", required=True)
    agent_line_categ = fields.Many2many(
        comodel_name='account.invoice.line.categ',
        relation='settlement_agent_line_categ_rel', column1='settlement_id',
        column2='agent_line_categ_id', required=True)
    date = fields.Date(compute='_compute_from_line', store=True)
    invoice_line = fields.Many2one(
        comodel_name='account.invoice.line', compute='_compute_from_line', store=True)
    invoice = fields.Many2one(
        comodel_name='account.invoice', compute='_compute_from_line', store=True, string="Invoice")
    agent = fields.Many2one(
        comodel_name="res.partner", readonly=True, compute='_compute_from_line',
        store=True)
    settled_amount = fields.Monetary(
        compute='_compute_from_line', readonly=True, store=True)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        compute='_compute_from_line',
        store=True,
        readonly=True,
    )
    commission = fields.Many2one(
        comodel_name="sale.commission", compute='_compute_from_line', store=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        related='settlement.company_id',
    )

    @api.depends('agent_line_categ', 'agent_line_categ.invoice_date',
                 'agent_line_categ.object_id', 'agent_line_categ.agent',
                 'agent_line_categ.amount', 'agent_line_categ.currency_id',
                 'agent_line_categ.commission')
    def _compute_from_line(self):
        for rec in self:
            line = rec.agent_line_categ[:1]  # take first record of M2M
            rec.date = line.invoice_date
            rec.invoice_line = line.object_id
            rec.invoice = line.object_id.invoice_id
            rec.agent = line.agent
            rec.settled_amount = sum(rec.agent_line_categ.mapped('amount'))
            rec.currency_id = line.currency_id
            rec.commission = line.commission

    @api.constrains('settlement', 'agent_line_categ')
    def _check_company(self):
        for record in self:
            for line in record.agent_line_categ:
                if line.company_id != record.company_id:
                    raise ValidationError(_("Company must be the same"))

class SettlementLine(models.Model):
    _inherit = "sale.commission.settlement.line"

    partner_id = fields.Many2one(
        related='invoice.partner_id',
        string="Partner",
        readonly=True,
    )
