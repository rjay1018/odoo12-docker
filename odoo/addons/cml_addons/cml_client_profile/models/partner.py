# -*- coding: utf-8 -*-

from odoo import models,fields,api


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    @api.multi
    def write(self, vals):
        if vals.get('support_ids') and (type(vals['support_ids']) is str) == True:
            support_list = []
            for id in vals.get('support_ids'):
                if id != ',' or id != '':
                    support_list.append(int(id))
            vals['support_ids'] = [[6, False, support_list]]
        if vals.get('birthday') == '':
            vals['birthday'] = False

        call_super = super(ResPartner, self).write(vals)
        return call_super