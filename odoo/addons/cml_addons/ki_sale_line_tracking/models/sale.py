from odoo import api, fields, models, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def _get_fields(self):
        list_of_fields = ['product_id', 'name', 'product_uom_qty', 'tax_id', 'product_uom', 'discount']
        return list_of_fields

    def write(self, vals):
        fields_data = self.fields_get()
        fields_list = self._get_fields()
        old_val = self.read(fields_list).pop()
        message = '<ul>'
        msg_lst = []
        for val in vals:
            if val in fields_list:
                if fields_data[val]['type'] == 'many2one':
                    if old_val:
                        if old_val[val]:
                            message += _('<li>' + fields_data[val]['string'] + ' : ' + old_val[val][
                                1] + ' ' + '<div class="o_Message_trackingValueSeparator o_Message_trackingValueItem fa fa-long-arrow-right" title="Changed" role="img"/>' +
                                         str(self.env[fields_data[val]['relation']].browse(
                                             vals[val]).display_name)) + '</li>'
                        else:
                            message += _('<li>' + fields_data[val][
                                'string'] + ' : ' + ' ' + '<div class="o_Message_trackingValueSeparator o_Message_trackingValueItem fa fa-long-arrow-right" title="Changed" role="img"/>' +
                                         str(self.env[fields_data[val]['relation']].browse(
                                             vals[val]).display_name)) + '</li>'
                    else:
                        message += _('<li>' + fields_data[val][
                            'string'] + ' : ' + ' ' + '<div class="o_Message_trackingValueSeparator o_Message_trackingValueItem fa fa-long-arrow-right" title="Changed" role="img"/>' +
                                     str(self.env[fields_data[val]['relation']].browse(
                                         vals[val]).display_name)) + '</li>'

                elif fields_data[val]['type'] == 'many2many':
                    if old_val:
                        old_id = self.env[fields_data[val]['relation']].browse(old_val[val])
                        new_id = self.env[fields_data[val]['relation']].browse(vals[val][0][2])
                        old_lis = old_id.mapped('name')
                        new_lis = new_id.mapped('name')
                        old_name = ','.join(old_lis)
                        new_name = ','.join(new_lis)
                        if old_val[val]:
                            message += _('<li>' + fields_data[val][
                                'string'] + ' : ' + old_name + ' ' + '<div class="o_Message_trackingValueSeparator o_Message_trackingValueItem fa fa-long-arrow-right" title="Changed" role="img"/>' +
                                         new_name + '</li>')
                        else:
                            message += _('<li>' + fields_data[val][
                                'string'] + ' : ' + ' ' + '<div class="o_Message_trackingValueSeparator o_Message_trackingValueItem fa fa-long-arrow-right" title="Changed" role="img"/>' +
                                         new_name + '</li>')
                    else:
                        message += _('<li>' + fields_data[val][
                            'string'] + ' : ' + ' ' + '<div class="o_Message_trackingValueSeparator o_Message_trackingValueItem fa fa-long-arrow-right" title="Changed" role="img"/>' +
                                     new_name + '</li>')
                else:
                    if fields_data[val]['type'] not in ['one2many']:
                        message += _('<li>' + fields_data[val]['string'] + ' : ' + str(old_val[
                                                                                           val]) + ' ' + '<div class="o_Message_trackingValueSeparator o_Message_trackingValueItem fa fa-long-arrow-right" title="Changed" role="img"/>' +
                                     str(vals[val])) + '</li>'
        message += '</ul>'
        msg_lst.append(message)
        if msg_lst:
            for msg in msg_lst:
                if msg != '<ul></ul>':
                    for rec in self:
                        if rec.order_id:
                            self.order_id.message_post(body=msg)
        return super(SaleOrderLine, self).write(vals)

    # def unlink(self):
    #     for rec in self:
    #         if rec.order_id:
    #             rec.order_id.message_post(
    #                 body='<ul>' + ' <li>' + rec.display_name + 'has been removed lines' + '</li>' + '</ul>')
    #     return super(SaleOrderLine, self).unlink()
