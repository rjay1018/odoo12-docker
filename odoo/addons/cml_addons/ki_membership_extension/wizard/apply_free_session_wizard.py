from odoo import api, fields, models, _


class ApplyFreeSession(models.TransientModel):
    _name = 'apply.free.session.wizard'
    _description = 'Apply Free Session Wizard'

    service_id = fields.Many2one(
        'product.product',
        string="service",
        required=True
    )

    unit_price = fields.Float(
        string="Price",
        required=True
    )

    def action_apply_free_session(self):
        active_id = self._context.get('active_id')
        if active_id:
            appointment_id = self.env['clinic.appointment'].browse(active_id)
            vals = {
                'appoint_id': appointment_id.id,
                'service_id': self.service_id.id,
                'unit_price': -self.unit_price,
                'invoiced_qty': 1
            }
            self.env['cml.multi.service.line'].create(vals)
