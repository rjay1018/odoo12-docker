# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api


class StockMoveGlobalWizardFail(models.TransientModel):
    _name = 'stock.move.global.wizard.fail'
    _description = 'Stock Move Quality Measurement Global check'

    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    sh_message = fields.Text('Measurement Message', readonly=True)
    sh_quality_point_id = fields.Many2one(
        'sh.qc.point', 'Quality Control Point')
    picking_id = fields.Many2one('stock.picking', 'Picking')
    picking_type_id = fields.Many2one('stock.picking.type')
    sh_measure = fields.Float('Measure', default=0.0)
    text_message = fields.Text("Enter QC details..")
    attachment_ids = fields.Many2many(
        'ir.attachment', string="Upload Pictures")
    type = fields.Selection([('type1', 'Pass-Fail'), ('type2', 'Measurement'),
                             ('type3', 'Take a Picture'), ('type4', 'Text')])
    move_id = fields.Many2one('stock.move')
    company_id = fields.Many2one(
        'res.company', string="Company", default=lambda self: self.env.user.company_id)
    ids_list = []

    @api.model
    def default_get(self, fields):
        res = super(StockMoveGlobalWizardFail, self).default_get(fields)
        context = self._context
        stock_move = self.env['stock.move'].sudo().search(
            [('id', '=', context.get('default_move_id'))], limit=1)

        quality_point_id = self.env['sh.qc.point'].sudo().search(
            [('product_id', '=', context.get('default_product_id')),
             ('operation', '=', context.get('default_transfer')),
             ('id', '=', context.get('default_point_id')),
             '|', ('team.user_ids.id', 'in', [self.env.uid]),
             ('team', '=', False)
             ], limit=1, order='name asc')
        if stock_move:
            if quality_point_id:
                res.update({
                    'product_id': quality_point_id.product_id.id,
                    'sh_quality_point_id': quality_point_id.id,
                    'sh_message': quality_point_id.sh_instruction,
                    'type': quality_point_id.type,
                    'picking_id': stock_move.picking_id.id,
                    'move_id': stock_move.id,

                })
            self.__class__.ids_list.append(context.get('default_point_id'))

        return res

    def action_pass(self):
        if self.picking_id:

            if self.type == 'type1':
                self.env['sh.quality.check'].sudo().create({
                    'product_id': self.product_id.id,
                    'sh_picking': self.picking_id.id,
                    'sh_control_point': self.sh_quality_point_id.name,
                    'control_point_id': self.sh_quality_point_id.id,
                    'sh_date': fields.Datetime.now(),
                    'sh_norm': 0.0,
                    'state': 'pass',
                    'qc_type': 'type1',
                    'company_id': self.env.user.company_id.id,
                    'sh_move_id': self.move_id.id

                })

            elif self.type == 'type3':
                self.env['sh.quality.check'].sudo().create({
                    'product_id': self.product_id.id,
                    'sh_picking': self.picking_id.id,
                    'sh_control_point': self.sh_quality_point_id.name,
                    'control_point_id': self.sh_quality_point_id.id,
                    'sh_date': fields.Datetime.now(),
                    'sh_norm': 0.0,
                    'state': 'pass',
                    'qc_type': 'type3',
                    'attachment_ids': [(6, 0, self.attachment_ids.ids)],
                    'company_id': self.env.user.company_id.id,
                    'sh_move_id': self.move_id.id

                })
                if self.attachment_ids:
                    if self.picking_id.attachment_ids:
                        self.picking_id.write({'attachment_ids': [
                            (6, 0, self.picking_id.attachment_ids.ids + self.attachment_ids.ids)]})
                    else:

                        self.picking_id.write(
                            {'attachment_ids': [(6, 0, self.attachment_ids.ids)]})
            elif self.type == 'type4':
                self.env['sh.quality.check'].sudo().create({
                    'product_id': self.product_id.id,
                    'sh_picking': self.picking_id.id,
                    'sh_control_point': self.sh_quality_point_id.name,
                    'control_point_id': self.sh_quality_point_id.id,
                    'sh_date': fields.Datetime.now(),
                    'sh_norm': 0.0,
                    'state': 'pass',
                    'qc_type': 'type4',
                    'text_message': self.text_message,
                    'company_id': self.env.user.company_id.id,
                    'sh_move_id': self.move_id.id

                })
            if self.picking_id:
                lines = self.env['sh.quality.check'].search([('control_point_id.id', 'not in', self.__class__.ids_list),
                                                             ('state', '=', 'fail'),
                                                             ('sh_picking', '=', self.picking_id.id),
                                                             ])

                if len(lines) > 0:
                    for i in lines:
                        if (i.control_point_id.number_of_test >= i.sh_move_id.count or i.control_point_id.number_of_test == 0) and (i.control_point_id.id not in \
                                [j.control_point_id for j in
                                 self.picking_id.sh_quality_check_ids.filtered(lambda k: k.state == 'pass')]):
                            return {
                                'name': 'Quality Check',
                                'type': 'ir.actions.act_window',
                                'view_type': 'form',
                                'view_mode': 'form',
                                'res_model': 'stock.move.global.wizard.fail',
                                'context': {
                                    'default_move_id': self.move_id.id,
                                    'default_picking_id': self.picking_id.id,
                                    'default_product_id': i.product_id.id,
                                    'default_point_id': i.control_point_id.id,
                                    'default_transfer': self._context.get('default_transfer'),
                                    'default_count': self._context.get('default_count')},
                                'target': 'new',
                            }
                    else:

                        self.__class__.ids_list.clear()
                        return {
                            'res_model': 'sh.quality.global.wizard.fail',
                            'type': 'ir.actions.act_window_close',
                        }
                else:

                    self.__class__.ids_list = []
                    return {
                        'res_model': 'stock.move.global.wizard.fail',
                        'type': 'ir.actions.act_window_close',
                    }

    def action_next(self):
        return True

    def action_validate(self):
        if self.picking_id:
            context = self._context
            if self.sh_measure >= self.sh_quality_point_id.sh_unit_from and self.sh_measure <= self.sh_quality_point_id.sh_unit_to:
                self.env['sh.quality.check'].sudo().create({
                    'product_id': self.product_id.id,
                    'sh_picking': self.picking_id.id,
                    'sh_control_point': self.sh_quality_point_id.name,
                    'control_point_id': self.sh_quality_point_id.id,
                    'sh_date': fields.Datetime.now(),
                    'sh_norm': self.sh_measure,
                    'state': 'pass',
                    'qc_type': 'type2',
                    'company_id': self.env.user.company_id.id,
                    'sh_move_id': self.move_id.id

                })
            else:
                self.env['sh.quality.check'].sudo().create({
                    'product_id': self.product_id.id,
                    'sh_picking': self.picking_id.id,
                    'sh_control_point': self.sh_quality_point_id.name,
                    'control_point_id': self.sh_quality_point_id.id,
                    'sh_date': fields.Datetime.now(),
                    'sh_norm': self.sh_measure,
                    'state': 'fail',
                    'qc_type': 'type2',
                    'company_id': self.env.user.company_id.id,
                    'sh_move_id': self.move_id.id

                })
                message = 'You Measured ' + str(self.sh_measure) + ' mm and it should be between ' + str(
                    self.sh_quality_point_id.sh_unit_from) + ' and ' + str(self.sh_quality_point_id.sh_unit_to) + ' mm.'

            if self.picking_id:
                lines = self.env['sh.quality.check'].search([('control_point_id', 'not in', self.__class__.ids_list),
                                                             ('state', '=', 'fail'),
                                                             ('sh_picking', '=', self.picking_id.id),
                                                             ])

                if len(lines) > 0:
                    for i in lines:
                        if (i.control_point_id.number_of_test >= i.sh_move_id.count or i.control_point_id.number_of_test == 0) and (
                                i.control_point_id.id not in \
                                [j.control_point_id for j in
                                 self.picking_id.sh_quality_check_ids.filtered(lambda k: k.state == 'pass')]):
                            return {
                                'name': 'Quality Check',
                                'type': 'ir.actions.act_window',
                                'view_type': 'form',
                                'view_mode': 'form',
                                'res_model': 'stock.move.global.wizard.fail',
                                'context': {
                                    'default_move_id': i.sh_move_id.id,
                                    'default_point_id': i.control_point_id.id,
                                    'default_product_id': i.product_id.id,
                                    'default_transfer': self._context.get('default_transfer'),
                                    'default_count': self._context.get('default_count')},
                                'target': 'new',
                            }
                    else:
                        self.__class__.ids_list.clear()
                        return {
                            'res_model': 'sh.quality.global.wizard.fail',
                            'type': 'ir.actions.act_window_close',
                        }
                else:

                    self.__class__.ids_list = []
                    return {
                        'res_model': 'stock.move.global.wizard.fail',
                        'type': 'ir.actions.act_window_close',
                    }

    def action_fail(self):
        if self.picking_id:
            if self.type == 'type1':
                self.env['sh.quality.check'].sudo().create({
                    'product_id': self.product_id.id,
                    'sh_picking': self.picking_id.id,
                    'sh_control_point': self.sh_quality_point_id.name,
                    'control_point_id': self.sh_quality_point_id.id,
                    'sh_date': fields.Datetime.now(),
                    'sh_norm': 0.0,
                    'state': 'fail',
                    'qc_type': 'type1',
                    'company_id': self.env.user.company_id.id,
                    'sh_move_id': self.move_id.id

                })
            elif self.type == 'type3':
                self.env['sh.quality.check'].sudo().create({
                    'product_id': self.product_id.id,
                    'sh_picking': self.picking_id.id,
                    'sh_control_point': self.sh_quality_point_id.name,
                    'control_point_id': self.sh_quality_point_id.id,
                    'sh_date': fields.Datetime.now(),
                    'sh_norm': 0.0,
                    'state': 'fail',
                    'qc_type': 'type3',
                    'attachment_ids': [(6, 0, self.attachment_ids.ids)],
                    'company_id': self.env.user.company_id.id,
                    'sh_move_id': self.move_id.id

                })
                if self.attachment_ids:
                    self.picking_id.write(
                        {'attachment_ids': [(6, 0, self.attachment_ids.ids)]})

            elif self.type == 'type4':
                self.env['sh.quality.check'].sudo().create({
                    'sh_move_id': self.move_id.id,
                    'product_id': self.product_id.id,
                    'sh_picking': self.picking_id.id,
                    'sh_control_point': self.sh_quality_point_id.name,
                    'control_point_id': self.sh_quality_point_id.id,
                    'sh_date': fields.Datetime.now(),
                    'sh_norm': 0.0,
                    'state': 'fail',
                    'qc_type': 'type4',
                    'text_message': self.text_message,
                    'company_id': self.env.user.company_id.id,
                    'sh_move_id': self.move_id.id

                })
            if self.picking_id:
                lines = self.env['sh.quality.check'].search([('control_point_id', 'not in', self.__class__.ids_list),
                                                             ('state', '=', 'fail'),
                                                             ('sh_picking', '=', self.picking_id.id),
                                                             ], order='control_point_id asc')

                if len(lines) > 0:
                    for i in lines:
                        if (i.control_point_id.number_of_test >= i.sh_move_id.count or i.control_point_id.number_of_test == 0) and (i.control_point_id.id not in \
                                [j.control_point_id for j in
                                 self.picking_id.sh_quality_check_ids.filtered(lambda k: k.state == 'pass')]):

                            return {
                                'name': 'Quality Check',
                                'type': 'ir.actions.act_window',
                                'view_type': 'form',
                                'view_mode': 'form',
                                'res_model': 'stock.move.global.wizard.fail',
                                'context': {
                                    'default_move_id': i.sh_move_id.id,
                                    'default_picking_id': self.picking_id.id,
                                    'default_product_id': i.product_id.id,
                                    'default_point_id': i.control_point_id.id,
                                    'default_transfer': self._context.get('default_transfer'),
                                    'default_count': self._context.get('default_count')},
                                'target': 'new',
                            }
                    else:
                        self.__class__.ids_list.clear()
                        return {
                            'res_model': 'sh.quality.global.wizard.fail',
                            'type': 'ir.actions.act_window_close',
                        }
                else:
                    self.__class__.ids_list = []
                    return {
                        'res_model': 'stock.move.global.wizard.fail',
                        'type': 'ir.actions.act_window_close',
                    }
