from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    total_free_session = fields.Float(
        string="Total Free Session",
        store=True,
        compute="_compute_total_free_session"
    )
    total_used_session = fields.Float(
        string="Total Used Session",
        store=True,
        compute="_compute_total_used_session"
    )
    total_available_session = fields.Float(
        string="Total Available Session",
        store=True,
        compute="_compute_total_available_session"

    )

    @api.depends('member_lines.free_session_number')
    def _compute_total_free_session(self):
        for record in self:
            record.total_free_session = sum(
                l.free_session_number
                for l in record.member_lines
            )

    @api.depends('member_lines.used_free_session')
    def _compute_total_used_session(self):
        for record in self:
            record.total_used_session = sum(
                l.used_free_session
                for l in record.member_lines
            )

    @api.depends('total_used_session', 'total_free_session')
    def _compute_total_available_session(self):
        for record in self:
            record.total_available_session = record.total_free_session - record.total_used_session
