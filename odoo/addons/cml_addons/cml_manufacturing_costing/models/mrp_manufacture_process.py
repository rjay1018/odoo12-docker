# -*- coding: utf-8 -*-
from odoo import models, api,fields, _
from odoo.exceptions import UserError


class MrpManufactureProcess(models.Model):
    _inherit = 'mrp.production'

    # product_uom_qty = fields.Float(string='Total Quantity', compute='_compute_product_uom_qty', store=True)

    @api.depends('pro_material_cost_ids', 'pro_material_cost_ids.total_cost', 'pro_material_cost_ids.total_actual_cost',
                 'pro_labour_cost_ids', 'pro_labour_cost_ids.total_cost', 'pro_labour_cost_ids.total_actual_cost',
                 'pro_overhead_cost_ids', 'pro_overhead_cost_ids.total_cost', 'pro_overhead_cost_ids.total_actual_cost')
    def _compute_total_cost(self):
        material_total = 0.0
        material_actual_total = 0.0

        labour_total = 0.0
        labour_actual_total = 0.0

        overhead_total = 0.0
        overhead_actual_total = 0.0

        for rec in self:

            for line in rec.pro_material_cost_ids:
                material_total += line.total_cost
                material_actual_total += line.total_actual_cost

            for line in rec.pro_labour_cost_ids:
                labour_total += line.total_cost
                labour_actual_total += line.total_actual_cost

            for line in rec.pro_overhead_cost_ids:
                overhead_total += line.total_cost
                overhead_actual_total += line.total_actual_cost

            rec.total_material_cost = material_total
            rec.total_actual_material_cost = material_actual_total

            rec.total_labour_cost = labour_total
            rec.total_actual_labour_cost = labour_actual_total

            rec.total_overhead_cost = overhead_total
            rec.total_actual_overhead_cost = overhead_actual_total


    product_expected_uom_id = fields.Many2one(
        'uom.uom', 'Product Expected Unit of Measure',
        related='product_id.uom_id',
        readonly=True, required=True,
        states={'confirmed': [('readonly', False)]})

    expected_cost = fields.Float(
        'Expected Cost', compute='get_expected_cost',
        default=0.0)

    def button_mark_done(self):
        for mo in self:
            for metcost in mo.pro_material_cost_ids:
                if metcost.actual_qty == 0.0:
                    metcost.actual_qty = metcost.planned_qty

            for metcost in mo.pro_overhead_cost_ids:
                if metcost.actual_qty == 0:
                    metcost.actual_qty = metcost.planned_qty

            for metcost in mo.pro_labour_cost_ids:
                if metcost.actual_qty == 0:
                    metcost.actual_qty = metcost.planned_qty

            if mo.product_id.valuation == 'real_time':
                mo._account_entry_move_cost()
#                 mo.product_id.standard_price = mo.expected_cost

            mo._compute_product_uom_qty()
# 
#             if mo.product_id.valuation == 'real_time':
#                 mo.product_id.standard_price = mo.expected_cost

        result = super(MrpManufactureProcess,self).button_mark_done()
#         for mo in self:
#             for metcost in mo.pro_material_cost_ids:
#                 if metcost.actual_qty == 0.0:
#                     metcost.actual_qty = metcost.planned_qty
# 
#             for metcost in mo.pro_overhead_cost_ids:
#                 if metcost.actual_qty == 0:
#                     metcost.actual_qty = metcost.planned_qty
# 
#             for metcost in mo.pro_labour_cost_ids:
#                 if metcost.actual_qty == 0:
#                     metcost.actual_qty = metcost.planned_qty
# 
#             if mo.product_id.valuation == 'real_time':
#                 mo._account_entry_move_cost()
# #                 mo.product_id.standard_price = mo.expected_cost

#             mo._compute_product_uom_qty()

#             if mo.expected_cost:
#                 mo.product_id.standard_price = mo.expected_cost

        return result

    # @api.depends('finished_move_line_ids', 'finished_move_line_ids.qty_done')
    def _compute_product_uom_qty(self):
        for rac in self:
            lines = rac.finished_move_line_ids.filtered(lambda i: i.product_id == rac.product_id)
            expected_qty = 0
            for l in lines:
                expected_qty += l.qty_done
            rac.product_uom_qty = expected_qty

    @api.multi
    @api.depends('total_actual_all_cost', 'product_uom_qty')
    def get_expected_cost(self):
        for rec in self:
            if rec.product_uom_qty != 0:
                rec.expected_cost = rec.total_actual_all_cost / rec.product_uom_qty


    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description):
        # This method returns a dictionary to provide an easy extension hook to modify the valuation lines (see purchase for an example)
        self.ensure_one()
        debit_line_vals = {
            'name': description,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.uom_id.id,
            'ref': description,
            'partner_id': partner_id,
            'debit': debit_value if debit_value > 0 else 0,
            'credit': -debit_value if debit_value < 0 else 0,
            'account_id': credit_account_id,
        }

        credit_line_vals = {
            'name': description,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.uom_id.id,
            'ref': description,
            'partner_id': partner_id,
            'credit': credit_value if credit_value > 0 else 0,
            'debit': -credit_value if credit_value < 0 else 0,
            'account_id':  debit_account_id,
        }

        rslt = {'credit_line_vals': credit_line_vals, 'debit_line_vals': debit_line_vals}
        if credit_value != debit_value:
            # for supplier returns of product in average costing method, in anglo saxon mode
            diff_amount = debit_value - credit_value
            price_diff_account = self.product_id.property_account_creditor_price_difference

            if not price_diff_account:
                price_diff_account = self.product_id.categ_id.property_account_creditor_price_difference_categ
            if not price_diff_account:
                raise UserError(_('Configuration error. Please configure the price difference account on the product or its category to process this operation.'))

            rslt['price_diff_line_vals'] = {
                'name': self.name,
                'product_id': self.product_id.id,
                'quantity': qty,
                'product_uom_id': self.product_id.uom_id.id,
                'ref': description,
                'partner_id': partner_id,
                'credit': diff_amount > 0 and diff_amount or 0,
                'debit': diff_amount < 0 and -diff_amount or 0,
                'account_id': price_diff_account.id,
            }
        return rslt

    def _prepare_account_move_line(self, cost, credit_account_id, debit_account_id, description):
        """
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given quant.
        """
        self.ensure_one()

        # the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
        # the company currency... so we need to use round() before creating the accounting entries.
        debit_value = self.company_id.currency_id.round(cost)
        credit_value = debit_value

        qty = 1
        valuation_partner_id = False
        res = [(0, 0, line_vals) for line_vals in self._generate_valuation_lines_data(valuation_partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description).values()]

        return res

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, cost, description):
        self.ensure_one()
        AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)

        move_lines = self._prepare_account_move_line(cost, credit_account_id, debit_account_id, description)
        if move_lines:
            date = self._context.get('force_period_date', fields.Date.context_today(self))
            new_account_move = AccountMove.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': description,
            })
            new_account_move.post()

    @api.multi
    def _get_accounting_data_for_valuation_cost(self, type):
        """ Return the accounts and journal to use to post Journal Entries for
        the real-time valuation of the quant. """
        self.ensure_one()
        tmpl_id = self.product_id.product_tmpl_id
        accounts_data = tmpl_id.get_product_accounts()

        debit_acc = False
        if type == 'overhead':
            debit_acc = tmpl_id.categ_id.account_overhead_cost_id.id
        else:
            debit_acc = tmpl_id.categ_id.account_labour_cost_id.id

        credit_acc= tmpl_id.categ_id.account_cost_id.id

        if not accounts_data.get('stock_journal', False):
            raise UserError(_('You don\'t have any stock journal defined on your product category, check if you have installed a chart of accounts.'))
        if not debit_acc:
            raise UserError(_('Cannot find a Labour/Overhead account on product category %s.') % (self.product_id.categ_id.display_name))
        if not credit_acc:
            raise UserError(_('Cannot find a Cost Valuation account on product category  %s.') % (self.product_id.categ_id.display_name))
        journal_id = accounts_data['stock_journal'].id
        return journal_id, debit_acc, credit_acc

    def _account_entry_move_cost(self):

        #overhead
        if self.total_actual_overhead_cost:
            description = "Overhead Cost"
            cost = self.total_actual_overhead_cost
            journal_id, debit_acc, credit_acc = self._get_accounting_data_for_valuation_cost(type="overhead")
            self.with_context(force_company=self.company_id.id)._create_account_move_line(credit_acc, debit_acc, journal_id, cost, description)

        #labour
        if self.total_actual_labour_cost:
            description = "Labour Cost"
            cost = self.total_actual_labour_cost
            journal_id, debit_acc, credit_acc = self._get_accounting_data_for_valuation_cost(type="labour")
            self.with_context(force_company=self.company_id.id)._create_account_move_line(credit_acc, debit_acc, journal_id, cost, description)
