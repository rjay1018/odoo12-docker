# -*- coding: utf-8 -*-
from odoo import models, fields


class ResUsers(models.Model):
    """Extend res.users to hold a whitelist of allowed journals per user.

    If a user belongs to the 'Restricted Journal Access' group, they will
    only be able to see the journals specifically mapped to them in this field.
    """
    _inherit = 'res.users'

    journal_ids = fields.Many2many(
        comodel_name='account.journal',
        relation='user_journal_restricted_rel',
        column1='user_id',
        column2='journal_id',
        string='Allowed Journals',
        help='Journals visible to this user when they belong to the '
             '"Restricted Journal Access" group.',
    )
