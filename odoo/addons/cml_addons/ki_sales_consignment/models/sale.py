# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    route_id = fields.Many2one(
        'stock.location.route',
        string="Route"
    )

    @api.onchange('partner_id')
    def _onchange_route(self):
        for rec in self:
            rec.route_id = rec.partner_id.route_id


class ResPartner(models.Model):
    _inherit = "res.partner"

    route_id = fields.Many2one(
        'stock.location.route',
        string="Route"
    )


class StockLocationRoute(models.Model):
    _inherit = "stock.location.route"

    show_on_customer = fields.Boolean(
        string='Show On Customer',
        copy=False
    )

    @api.onchange('sale_selectable')
    def _onchange_show_on_customer(self):
        if not self.sale_selectable:
            self.show_on_customer = False


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def create(self, vals):
        if 'picking_id' in vals:
            picking = self.env['stock.picking'].browse(vals['picking_id'])
            vals.update({
                'partner_id': picking.partner_id.id
            })
        return super(StockMove, self).create(vals)

