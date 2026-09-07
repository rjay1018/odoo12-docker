from odoo import models, fields, api, _

class BIRReportTemplate(models.Model):
    _name = 'bir.report.template'
    _description = 'BIR Report Template'

    name = fields.Char(string="Name", required=True)
    filename = fields.Char(string="Filename", required=True)
    file = fields.Binary(string="File", required=True)
    type = fields.Selection([('2307', '2307 Form')], string="Type", required=True)
    company_profile_name = fields.Char(string="Company Profile Name")
    company_position_name = fields.Char(string="Company Position Name")

class AccountTax(models.Model):
    _inherit = 'account.tax'

    tax_report_description = fields.Char(string="Description")
    show_in_tax_report = fields.Boolean(string="Show in Tax Report")

class AccountInvoiceTax(models.Model):
    _inherit = 'account.invoice.tax'

    description = fields.Char(string="Description", related="tax_id.tax_report_description")

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def action_open_bir_report_wizard(self):
        return {
            'name': 'BIR Report Wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'bir.report.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('cml_bir_reports.view_bir_report_wizard_form').id,
            'target': 'new',
            'context': {'default_invoice_id': self.id},  # Pass invoice ID if needed
        }

