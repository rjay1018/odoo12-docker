from odoo import models, fields, api, tools, _


class NightDiffPayRate(models.Model):
    _name = 'hr.nd.pay.rate'

    @api.multi
    @api.depends('name', 'rate')
    def name_get(self):
        res = []
        for r in self:
            name = "%s (%s)" % (r.name, r.rate)
            res += [(r.id, name)]
        return res

    name = fields.Char(required=True)
    rate = fields.Float('Rate (%)', required=True)
