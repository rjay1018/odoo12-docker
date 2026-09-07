from odoo import models, fields, api
from odoo.exceptions import UserError

class ChangeInvoiceJournalWizard(models.TransientModel):
    _name = 'change.invoice.journal.wizard'
    _description = 'Change Invoice Journal Wizard'

    journal_id = fields.Many2one(
        'account.journal',
        string='New Journal',
        required=True,
        domain="[('type', '=', 'sale')]"
    )
    invoice_ids = fields.Many2many('account.invoice', string='Invoices')

    def apply_journal_change(self):
        self.ensure_one()
        journal = self.journal_id

        if journal.type != 'sale':
            raise UserError("Selected journal is not of type 'sale'.")

        cr = self.env.cr

        for invoice in self.invoice_ids:
            # Update account.invoice
            cr.execute("""
                UPDATE account_invoice
                SET journal_id = %s
                WHERE id = %s
            """, (journal.id, invoice.id))

            # Update account.move
            if invoice.move_id:
                cr.execute("""
                    UPDATE account_move
                    SET journal_id = %s
                    WHERE id = %s
                """, (journal.id, invoice.move_id.id))

                # Update account.move.line
                cr.execute("""
                    UPDATE account_move_line
                    SET journal_id = %s
                    WHERE move_id = %s
                """, (journal.id, invoice.move_id.id))

        cr.commit()
