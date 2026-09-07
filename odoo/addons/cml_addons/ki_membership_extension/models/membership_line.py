from odoo import models, fields, api


class MembershipLine(models.Model):
    _inherit = "membership.membership_line"

    is_apply_free_session = fields.Boolean(
        string='Give Free Session?',
        related="membership_id.is_apply_free_session"

    )
    free_session_number = fields.Integer(
        string='Free Sessions',
        related="membership_id.free_session_number"
    )
    used_free_session = fields.Integer(
        string='Used Free Sessions',

    )
