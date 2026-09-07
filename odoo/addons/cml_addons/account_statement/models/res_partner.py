# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from odoo.tools.float_utils import float_round as round
from odoo import api, fields, models, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import base64
import re
import calendar
import logging

_logger = logging.getLogger(__name__)

class CustomerStatementDays(models.Model):
    _name = 'statement.days'
    customer_id = fields.Many2one('res.partner')

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _get_result(self):
        for invoice in self:
            invoice.result = invoice.amount_total_signed - invoice.credit_amount

    @api.multi
    def _get_credit(self):
        for invoice in self:
            invoice.credit_amount = invoice.amount_total_signed - invoice.residual_signed

    credit_amount = fields.Float(compute='_get_credit', string="Credit/Paid")
    result = fields.Float(compute='_get_result', string="Balance")  # 'balance' field is not the same

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def _get_amounts_and_date_amount(self):
        user_id = self._uid
        company = self.env['res.users'].browse(user_id).company_id
        current_date = date.today()

        for partner in self:
            # Process monthly statement filter only if necessary
            if not partner.monthly_statement_line_ids:
                partner.do_process_monthly_statement_filter()

            amount_due = amount_overdue = 0.0
            supplier_amount_due = supplier_amount_overdue = 0.0

            # Calculate customer invoices
            for aml in partner.balance_invoice_ids.filtered(lambda x: x.company_id == company):
                date_maturity = aml.date_due or aml.date
                amount_due += aml.result
                if date_maturity <= current_date:
                    amount_overdue += aml.residual

            partner.payment_amount_due_amt = amount_due
            partner.payment_amount_overdue_amt = amount_overdue

            # Calculate supplier invoices
            for aml in partner.supplier_invoice_ids.filtered(lambda x: x.company_id == company):
                date_maturity = aml.date_due or aml.date
                supplier_amount_due += aml.result
                if date_maturity <= current_date:
                    supplier_amount_overdue += aml.residual

            partner.payment_amount_due_amt_supplier = supplier_amount_due
            partner.payment_amount_overdue_amt_supplier = supplier_amount_overdue

            # Calculate monthly statement lines
            monthly_amount_due_amt = monthly_amount_overdue_amt = 0.0
            for aml in partner.monthly_statement_line_ids:
                date_maturity = aml.date_due
                monthly_amount_due_amt += aml.result
                if date_maturity and date_maturity <= current_date:
                    monthly_amount_overdue_amt += aml.result

            partner.monthly_payment_amount_due_amt = monthly_amount_due_amt
            partner.monthly_payment_amount_overdue_amt = monthly_amount_overdue_amt

    @api.multi
    def do_button_print_statement(self):
        if self.customer:
            return self.env.ref('account_statement.report_customert_print').report_action(self)

    def do_button_print_statement_vendor(self):
        if self.supplier:
            return self.env.ref('account_statement.report_supplier_print').report_action(self)

    start_date = fields.Date('Start Date', compute='get_dates')
    month_name = fields.Char('Month', compute='get_dates')
    end_date = fields.Date('End Date', compute='get_dates')
    monthly_statement_line_ids = fields.One2many('monthly.statement.line', 'partner_id', 'Monthly Statement Lines')
    supplier_invoice_ids = fields.One2many(
        'account.invoice', 'partner_id', 'Supplier Invoices',
        domain=[('type', 'in', ['in_invoice', 'in_refund']), ('state', 'in', ['open', 'paid'])]
    )
    balance_invoice_ids = fields.One2many(
        'account.invoice', 'partner_id', 'Customer Invoices',
        domain=[('type', 'in', ['out_invoice', 'out_refund']), ('state', 'in', ['open', 'paid'])]
    )
    customer_state_ids = fields.One2many(
        'account.move.line', 'partner_id', 'Customer Move Lines',
        domain=[('reconciled', '=', False), ('account_id.internal_type', '=', 'receivable')]
    )
    unreconciled_aml_ids = fields.One2many('account.move.line', 'partner_id', 'Move Lines')
    payment_amount_due_amt = fields.Float(compute='_get_amounts_and_date_amount', string="Balance Due")
    payment_amount_overdue_amt = fields.Float(compute='_get_amounts_and_date_amount', string="Total Overdue Amount")
    payment_amount_due_amt_supplier = fields.Float(compute='_get_amounts_and_date_amount', string="Supplier Balance Due")
    payment_amount_overdue_amt_supplier = fields.Float(compute='_get_amounts_and_date_amount', string="Total Supplier Overdue Amount")
    monthly_payment_amount_due_amt = fields.Float(compute='_get_amounts_and_date_amount', string="Balance Due")
    monthly_payment_amount_overdue_amt = fields.Float(compute='_get_amounts_and_date_amount', string="Total Overdue Amount")
    current_date = fields.Date(default=fields.date.today())
    first_thirty_day = fields.Float(string="0-30", compute="compute_zero_thirty_days")
    thirty_sixty_days = fields.Float(string="30-60", compute="compute_thirty_sixty_days")
    sixty_ninty_days = fields.Float(string="60-90", compute="compute_sixty_ninty_days")
    ninty_plus_days = fields.Float(string="90+", compute="compute_ninty_plus_days")
    total = fields.Float(string="Total", compute="compute_total")

    @api.multi
    def get_dates(self):
        for record in self:
            today = date.today()
            d = today - relativedelta(months=1)
            start_date = date(d.year, d.month, 1)
            end_date = date(today.year, today.month, 1) - relativedelta(days=1)
            record.month_name = calendar.month_name[start_date.month]
            record.start_date = str(start_date)
            record.end_date = str(end_date)

    @api.one
    @api.depends('balance_invoice_ids')
    def compute_zero_thirty_days(self):
        today = fields.date.today()
        self.first_thirty_day = sum(
            line.result for line in self.balance_invoice_ids
            if 0 < (today - fields.Date.from_string(line.date_due)).days <= 30
        )

    @api.one
    @api.depends('balance_invoice_ids')
    def compute_thirty_sixty_days(self):
        today = fields.date.today()
        self.thirty_sixty_days = sum(
            line.result for line in self.balance_invoice_ids
            if 30 < (today - fields.Date.from_string(line.date_due)).days <= 60
        )

    @api.one
    @api.depends('balance_invoice_ids')
    def compute_sixty_ninty_days(self):
        today = fields.date.today()
        self.sixty_ninty_days = sum(
            line.result for line in self.balance_invoice_ids
            if 60 < (today - fields.Date.from_string(line.date_due)).days <= 90
        )

    @api.one
    @api.depends('balance_invoice_ids')
    def compute_ninty_plus_days(self):
        today = fields.date.today()
        self.ninty_plus_days = sum(
            line.result for line in self.balance_invoice_ids
            if (today - fields.Date.from_string(line.date_due)).days > 90
        )

    @api.one
    @api.depends('ninty_plus_days', 'sixty_ninty_days', 'thirty_sixty_days', 'first_thirty_day')
    def compute_total(self):
        self.total = self.ninty_plus_days + self.sixty_ninty_days + self.thirty_sixty_days + self.first_thirty_day

    @api.model
    def _cron_send_customer_statement(self):
        partners = self.search([('customer', '=', True)])
        if self.env.user.company_id.period == 'monthly':
            partners.do_process_monthly_statement_filter()
            partners.customer_monthly_send_mail()

        attachment_obj = self.env['ir.attachment']
        for record in partners:
            ir_actions_report = self.env['ir.actions.report']
            matching_reports = ir_actions_report.search([('report_name', '=', 'account_statement.monthly_customer_statement')])
            if matching_reports:
                report = matching_reports[0]
                try:
                    result, format = report.render_qweb_pdf([record.id])
                    result = base64.b64encode(result)
                    file_name = re.sub(r'[^a-zA-Z0-9_-]', '_', "Customer Monthly Statement") + ".pdf"
                    attachment_obj.create({
                        'name': file_name,
                        'datas': result,
                        'datas_fname': file_name,
                        'res_model': 'res.partner',
                        'res_id': record.id,
                        'type': 'binary'
                    })
                except Exception as e:
                    _logger.error(f"Failed to generate PDF for partner ID {record.id}: {e}")

        partners.customer_send_mail()
        return True

    @api.multi
    def customer_monthly_send_mail(self):
        unknown_mails = 0
        for partner in self:
            partners_to_email = [child for child in partner.child_ids if child.type == 'invoice' and child.email]
            if not partners_to_email and partner.email:
                partners_to_email = [partner]

            for partner_to_email in partners_to_email:
                try:
                    mail_template_id = self.env['ir.model.data'].xmlid_to_object('account_statement.email_template_customer_monthly_statement')
                    mail_template_id.send_mail(partner_to_email.id)
                except Exception as e:
                    _logger.error(f"Failed to send email to {partner_to_email.email}: {e}")
                    unknown_mails += 1
        return unknown_mails

    @api.multi
    def do_process_monthly_statement_filter(self):
        account_invoice_obj = self.env['account.invoice']
        statement_line_obj = self.env['monthly.statement.line']

        for record in self:
            # Calculate the date range for the previous month
            today = date.today()
            d = today - relativedelta(months=1)
            start_date = date(d.year, d.month, 1)
            end_date = date(today.year, today.month, 1) - relativedelta(days=1)
            from_date = str(start_date)
            to_date = str(end_date)

            # Domain to filter invoices for the previous month
            domain = [
                ('type', 'in', ['out_invoice', 'out_refund']),
                ('state', 'in', ['open', 'paid']),
                ('partner_id', '=', record.id),
                ('date_invoice', '>=', from_date),
                ('date_invoice', '<=', to_date),
            ]
            invoices = account_invoice_obj.search(domain)

            # Fetch existing monthly statement lines for the partner
            existing_lines = statement_line_obj.search([('partner_id', '=', record.id)])
            existing_line_map = {line.invoice_id.id: line for line in existing_lines}

            # Process each invoice
            for invoice in invoices.sorted(key=lambda r: r.number):
                vals = {
                    'partner_id': invoice.partner_id.id or False,
                    'state': invoice.state or False,
                    'date_invoice': invoice.date_invoice,
                    'date_due': invoice.date_due,
                    'number': invoice.number or '',
                    'result': invoice.result or 0.0,
                    'name': invoice.name or '',
                    'amount_total': invoice.amount_total or 0.0,
                    'credit_amount': invoice.credit_amount or 0.0,
                    'invoice_id': invoice.id,
                }
                if invoice.id in existing_line_map:
                    # Update the existing line
                    existing_line_map[invoice.id].write(vals)
                    del existing_line_map[invoice.id]  # Remove from the map as it's processed
                else:
                    # Create a new line if no matching record exists
                    statement_line_obj.create(vals)

            # Delete any remaining lines that were not matched to an invoice
            lines_to_delete = existing_line_map.values()
            for line in lines_to_delete:
                line.unlink()

    @api.multi
    def customer_send_mail(self):
        unknown_mails = 0
        for partner in self:
            partners_to_email = [child for child in partner.child_ids if child.type == 'invoice' and child.email]
            if not partners_to_email and partner.email:
                partners_to_email = [partner]

            for partner_to_email in partners_to_email:
                try:
                    mail_template_id = self.env['ir.model.data'].xmlid_to_object('account_statement.email_template_customer_statement')
                    mail_template_id.send_mail(partner_to_email.id)
                except Exception as e:
                    _logger.error(f"Failed to send email to {partner_to_email.email}: {e}")
                    unknown_mails += 1
        return unknown_mails

    @api.multi
    def supplier_send_mail(self):
        unknown_mails = 0
        for partner in self:
            partners_to_email = [child for child in partner.child_ids if child.type == 'invoice' and child.email]
            if not partners_to_email and partner.email:
                partners_to_email = [partner]

            for partner_to_email in partners_to_email:
                try:
                    mail_template_id = self.env['ir.model.data'].xmlid_to_object('account_statement.email_template_supplier_statement')
                    mail_template_id.send_mail(partner_to_email.id)
                except Exception as e:
                    _logger.error(f"Failed to send email to {partner_to_email.email}: {e}")
                    unknown_mails += 1
        return unknown_mails