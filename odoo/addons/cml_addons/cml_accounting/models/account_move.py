# -*- coding: utf-8 -*-
from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'


    @api.multi
    def remove_move_reconcile(self):
        _logger.info(">>> Executing custom remove_move_reconcile for move_lines: %s", self.ids)
        # Unreconciling may attempt to update amount_residual and debit_cash_basis on closed period lines.
        # Disabling check_move_validity prevents lock date constraint errors during this process.
        # Disabling auditlog prevents nested recompute CacheMiss loops when auditlog intercepts read().
        res = super(AccountMoveLine, self.with_context(check_move_validity=False, auditlog_disabled=True)).remove_move_reconcile()
        
        # Odoo 12 Bug Fix: Unlinking partial reconciles deletes the exchange rate move and its lines.
        # However, these deleted move lines might still be marked for recomputation (env.all.todo)
        # or marked as dirty (env.dirty). This causes flush() to crash with CacheMiss later.
        # We must aggressively clean up these environments for any deleted records.
        
        # 1. Clean up env.all.todo
        if hasattr(self.env, 'all') and hasattr(self.env.all, 'todo'):
            for field, recs_list in list(self.env.all.todo.items()):
                for i, recs in enumerate(recs_list):
                    deleted = recs.filtered(lambda r: not r.exists())
                    if deleted:
                        recs_list[i] = recs - deleted

        # 2. Clean up env.dirty
        if hasattr(self.env, 'dirty'):
            for record in list(self.env.dirty.keys()):
                if not record.exists():
                    del self.env.dirty[record]
                    
        return res
