from odoo import models, fields, api



class MultiServiceLine(models.Model):
    _inherit = "cml.multi.service.line"

    is_free_session_line = fields.Boolean(string="Free Session Line?")

class ClinicAppointment(models.Model):
    _inherit = "clinic.appointment"

    available_session = fields.Float(
        string="Available Session",
        related="partner_id.total_available_session",
        store=True
    )
    def actin_apply_free_session(self):
        for rec in self:
            if any(i.is_free_session_line for i in rec.multi_service_ids):
                return True
            if rec.partner_id:
                for membership in rec.partner_id.member_lines:
                    if membership.date_to > fields.Date.today():
                        if membership.is_apply_free_session:
                            if membership.used_free_session < membership.free_session_number:
                                if rec.product_id.id in membership.membership_id.allow_free_session_product_ids.ids:
                                    vals = {
                                        'appoint_id': self.id,
                                        'service_id': membership.membership_id.free_product_id.id,
                                        'unit_price': rec.product_id.lst_price,
#                                         'invoiced_qty': -1,
                                        'is_free_session_line': True,
                                        'qty': -1
                                    }
                                    self.env['cml.multi.service.line'].create(vals)
                                    membership.used_free_session += 1
