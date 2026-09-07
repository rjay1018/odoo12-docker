from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class request_partner(models.TransientModel):

    _name = "request.partner"

    partner_id = fields.Many2one(
        'res.partner',
        string="Vendor",
        required=True
    )

    @api.multi
    def submit_record(self):
        active_ids = self.env.context.get('active_ids', [])
        active_record = self.env['maintenance.request'].browse(active_ids)

        if not active_record.additional_spare_part_id:
            raise ValidationError(_('Please add at least one spare part to create PO'))

        order_id = self.env['purchase.order'].create({
            'partner_id': self.partner_id.id,
            'date_order': fields.Date.today(),
            'maintenance_request_id' : active_record.id
        })
        order_line_obj = self.env['purchase.order.line']

        for record in active_record.additional_spare_part_id:
            if record.po_line_id and record.po_line_id.order_id.state != 'cancel':
                pass

            if not record.spare_part_id.related_product_id:
                raise ValidationError(_('Please set Related Product on Spare Part: %s' %record.spare_part_id.name))

            line_val = {
                'product_id': record.spare_part_id.related_product_id.id,
                'order_id': order_id.id
            }
            order_line_new = order_line_obj.new(line_val)
            order_line_new.onchange_product_id()
            order_line_new.product_qty = record.quantity
            order_line_new._onchange_quantity()
            order_line_new.price_unit = record.price
            order_line_values = order_line_new._convert_to_write(order_line_new._cache)
            po_line =order_line_obj.create(order_line_values)
            record.po_line_id = po_line.id
        act = self.env.ref('purchase.purchase_rfq').read([])[0]
        act['domain'] = [('id', 'in', order_id.ids)]
        return act

