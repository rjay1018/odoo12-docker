# -*- coding: utf-8 -*-
# Copyright 2017 Renato B. Lopez Jr. CML - Transformative Coaching and Consulting Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ResPartnerRef(models.Model):

    _inherit = "res.partner"

    ref = fields.Char(
        string='Partner Code',
        default=lambda self: ('/')
    )

    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
            Use the sequence field in the searching for the partner
            in the relationship fields from res.partner
        """
        records = super(ResPartnerRef, self).name_search(name, args,
                                                   operator=operator,
                                                   limit=limit)
        recs = []
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
            recs = self.search([('ref', operator, name)], limit=limit)
            recs = recs.name_get()
        return records + recs

    @api.model
    def create(self, vals):
        """
        Assign the contact a new sequence number if the contact is a customer

        :param vals: the new record values
        :return: created record
        :rtype: res.partner model
        """
        record = super(ResPartnerRef, self).create(vals)
        # pylint: disable=no-member
        if record.customer and record.ref == "/":
            record.ref = self.env['ir.sequence'].next_by_code('partner.ref.sequence')
        return record
