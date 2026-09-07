from odoo import api, fields, models, _
from lxml import etree
import json


class KiSaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(selection_add=[('franchise_confirmed', 'Franchise Confirmed')])

    def franchise_confirmed(self):
        for rec in self:
            rec.state = 'franchise_confirmed'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(KiSaleOrder, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if self.env.user.has_group("cml_yyy.group_franchise_user"):
            doc = etree.XML(res['arch'])
            for field in res['fields']:
                for node in doc.xpath("//field[@name='%s']" % field):
                    node.set("readonly", "1")
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers['readonly'] = [('state', '=', 'franchise_confirmed')]
                    node.set("modifiers", json.dumps(modifiers))
            res['arch'] = etree.tostring(doc)
        return res

