# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _


class ShQualityGlobalWizardFail(models.TransientModel):
    _name = 'sh.quality.global.wizard.fail'
    _description = 'Stock Move Quality Measurement Global check if Fail'

    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    sh_message = fields.Text('Measurement Message', readonly=True)
    sh_quality_point_id = fields.Many2one(
        'sh.qc.point', 'Quality Control Point')
    picking_id = fields.Many2one('stock.picking', 'Picking')
    sh_measure = fields.Float('Measure', default=0.0)
    text_message = fields.Text("Enter QC details..")
    attachment_ids = fields.Many2many(
        'ir.attachment', string="Upload Pictures")
    type = fields.Selection([('type1', 'Pass-Fail'), ('type2', 'Measurement'),
                             ('type3', 'Take a Picture'), ('type4', 'Text')])
    mrp_id = fields.Many2one('mrp.production')
    workorder_id = fields.Many2one('mrp.workorder')
    company_id = fields.Many2one(
        'res.company', string="Company", default=lambda self: self.env.user.company_id)
    ids_list = []
    workorder_ids_list = []

    @api.model
    def default_get(self, fields):
        res = super(ShQualityGlobalWizardFail, self).default_get(fields)
        context = self._context
        mrp_id = self.env['mrp.production'].sudo().search(
            [('id', '=', context.get('default_mrp_id'))], limit=1)
        workorder_id = self.env['mrp.workorder'].sudo().search(
            [('id', '=', context.get('default_workorder_id'))], limit=1)

        if mrp_id:
            quality_point_id = self.env['sh.qc.point'].sudo().search([('product_id', '=', mrp_id.product_id.id),
                                                                      ('id', '=', context.get('default_point_id')),
                                                                      ('operation.name', '=', 'Manufacturing'),
                                                                      '|', ('team.user_ids.id', 'in', [self.env.uid]),
                                                                      ('team', '=', False),

                                                                      ], limit=1, order='create_date desc')
            if quality_point_id:
                res.update({
                    'product_id': quality_point_id.product_id.id,
                    'sh_quality_point_id': quality_point_id.id,
                    'sh_message': quality_point_id.sh_instruction,
                    'type': quality_point_id.type,
                    'mrp_id': mrp_id.id,

                    # 'picking_id': mrp_id.picking_id.id
                })
                self.__class__.ids_list.append(context.get('default_point_id'))



        elif workorder_id:
            work_quality_point_id = self.env['sh.qc.point'].sudo().search(
                [('product_id', '=', workorder_id.product_id.id),
                 ('id', '=', context.get('default_point_id')),
                 ('operation.id', '=', context.get('default_transfer')),
                 '|', ('team.user_ids.id', 'in', [self.env.uid]),
                 ('team', '=', False)
                 ], limit=1, order='create_date desc')
            if work_quality_point_id:
                res.update({
                    'product_id': work_quality_point_id.product_id.id,
                    'sh_quality_point_id': work_quality_point_id.id,
                    'sh_message': work_quality_point_id.sh_instruction,
                    'type': work_quality_point_id.type,
                    'workorder_id': workorder_id.id,
                    # 'picking_id': mrp_id.picking_id.id
                })
                self.__class__.ids_list.append(context.get('default_point_id'))
        return res

    def action_pass(self):
        if self.type == 'type1' and self.mrp_id:
            self.env['sh.mrp.quality.check'].create({
                'product_id': self.product_id.id,
                # 'sh_workorder_id': self.workorder_id.id,
                'sh_control_point': self.sh_quality_point_id.name,
                'control_point_id': self.sh_quality_point_id.id,
                'sh_date': fields.Datetime.now(),
                'sh_norm': 0.0,
                'sh_mrp': self._context.get('default_mrp_id'),
                'state': 'pass',
                'qc_type': 'type1'
            })
        elif self.type == 'type3' and self.mrp_id:
            lines = []
            for rec in self.attachment_ids:
                lines.append(rec.id)
            attachment_ids = [(6, 0, lines)]
            self.env['sh.mrp.quality.check'].sudo().create({
                'product_id': self.product_id.id,
                'id': self._context.get('default_id'),
                # 'sh_workorder_id': self.workorder_id.id,
                'sh_control_point': self.sh_quality_point_id.name,
                'control_point_id': self.sh_quality_point_id.id,
                'attachment_ids': attachment_ids,
                'sh_date': fields.Datetime.now(),
                'sh_norm': 0.0,
                'sh_mrp': self._context.get('default_mrp_id'),
                'state': 'pass',
                'qc_type': 'type3',

            })

            if self.attachment_ids:
                if self.mrp_id.attachment_ids:

                    self.mrp_id.write({'attachment_ids': [
                        (6, 0, self.mrp_id.attachment_ids.ids + self.attachment_ids.ids)]})
                else:
                    self.mrp_id.write({'attachment_ids': [(6, 0, self.attachment_ids.ids)]})

        elif self.type == 'type4' and self.mrp_id:
            self.env['sh.mrp.quality.check'].sudo().create({
                'product_id': self.product_id.id,
                ''
                'sh_picking': self.picking_id.id,
                'sh_control_point': self.sh_quality_point_id.name,
                'control_point_id': self.sh_quality_point_id.id,
                'sh_date': fields.Datetime.now(),
                'sh_norm': 0.0,
                'state': 'pass',
                'sh_mrp': self._context.get('default_mrp_id'),
                'qc_type': 'type4',
                'text_message': self.text_message,
            })
        elif self.type == 'type1' and self.workorder_id:
            self.env['sh.mrp.quality.check'].create({
                'product_id': self.product_id.id,
                # 'sh_workorder_id': self.workorder_id.id,
                'sh_control_point': self.sh_quality_point_id.name,
                'control_point_id': self.sh_quality_point_id.id,
                'sh_date': fields.Datetime.now(),
                'sh_norm': 0.0,
                'sh_workorder_id': self._context.get('default_workorder_id'),
                'state': 'pass',
                'qc_type': 'type1'
            })
        elif self.type == 'type3' and self.workorder_id:
            lines = []
            for rec in self.attachment_ids:
                lines.append(rec.id)
            attachment_ids = [(6, 0, lines)]
            self.env['sh.mrp.quality.check'].sudo().create({
                'product_id': self.product_id.id,
                # 'sh_workorder_id': self.workorder_id.id,
                'sh_control_point': self.sh_quality_point_id.name,
                'control_point_id': self.sh_quality_point_id.id,
                'attachment_ids': attachment_ids,
                'sh_date': fields.Datetime.now(),
                'sh_norm': 0.0,
                'sh_workorder_id': self._context.get('default_workorder_id'),
                'state': 'pass',
                'qc_type': 'type3',

            })
            if self.attachment_ids:
                if self.workorder_id.attachment_ids:

                    self.workorder_id.write({'attachment_ids': [
                        (6, 0, self.workorder_id.attachment_ids.ids + self.attachment_ids.ids)]})
                else:
                    self.workorder_id.write({'attachment_ids': [(6, 0, self.attachment_ids.ids)]})

        elif self.type == 'type4' and self.workorder_id:
            self.env['sh.mrp.quality.check'].sudo().create({
                'product_id': self.product_id.id,
                'sh_picking': self.picking_id.id,
                'sh_control_point': self.sh_quality_point_id.name,
                'control_point_id': self.sh_quality_point_id.id,
                'sh_date': fields.Datetime.now(),
                'sh_norm': 0.0,
                'state': 'pass',
                'sh_workorder_id': self._context.get('default_workorder_id'),
                'qc_type': 'type4',
                'text_message': self.text_message,
            })
        if self.mrp_id:
            lines = self.env['sh.mrp.quality.check'].search([('control_point_id', 'not in', self.__class__.ids_list),
                                                             ('sh_mrp', '=', self.mrp_id.id),
                                                             ('state', '=', 'fail'),
                                                             ('product_id', '=', self.product_id.id),
                                                             ])

            if len(lines) > 0:
                for i in lines:
                    if i.control_point_id.number_of_test >= self._context.get('default_count') or i.control_point_id.number_of_test == 0:
                        return {
                            'name': 'Quality Check',
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'sh.quality.global.wizard.fail',
                            'context': {'default_mrp_id': self.mrp_id.id,
                                        'default_point_id': i.control_point_id.id, 'default_count':
                                            self._context.get('default_count')},
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
                    'res_model': 'sh.quality.global.wizard.fail',
                    'type': 'ir.actions.act_window_close',
                }
        if self.workorder_id:
            lines = self.env['sh.mrp.quality.check'].search([('control_point_id', 'not in', self.__class__.ids_list),
                                                             ('product_id', '=', self.product_id.id,
                                                              ),
                                                             ('sh_workorder_id', '=', self.workorder_id.id),
                                                             ('state', '=', 'fail'),
                                                             ])

            if len(lines) > 0:
                for i in lines:
                    if i.control_point_id.number_of_test >= self._context.get('default_count') \
                            or i.control_point_id.number_of_test == 0:
                        return {
                            'name': 'Quality Check',
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'sh.quality.global.wizard.fail',
                            'context': {'default_workorder_id': self.workorder_id.id,
                                        'default_point_id': i.control_point_id.id,
                                        'default_transfer': i.control_point_id.operation.id,
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
                    'res_model': 'sh.quality.global.wizard.fail',
                    'type': 'ir.actions.act_window_close',
                }

    def action_validate(self):
        context = self._context
        if self.sh_measure >= self.sh_quality_point_id.sh_unit_from and self.sh_measure <= self.sh_quality_point_id.sh_unit_to and self.mrp_id:
            self.env['sh.mrp.quality.check'].sudo().create({
                'product_id': self.product_id.id,
                'sh_picking': self.picking_id.id,
                'sh_control_point': self.sh_quality_point_id.name,
                'control_point_id': self.sh_quality_point_id.id,
                'sh_date': fields.Datetime.now(),
                'sh_norm': self.sh_measure,
                'sh_mrp': self._context.get('default_mrp_id'),
                'state': 'pass',
                'qc_type': 'type2',
                'company_id': self.env.user.company_id.id,

            })

        elif self.mrp_id:
            self.env['sh.mrp.quality.check'].sudo().create({
                'product_id': self.product_id.id,
                'sh_picking': self.picking_id.id,
                'sh_control_point': self.sh_quality_point_id.name,
                'control_point_id': self.sh_quality_point_id.id,
                'sh_date': fields.Datetime.now(),
                'sh_norm': self.sh_measure,
                'sh_mrp': self._context.get('default_mrp_id'),
                'state': 'fail',
                'qc_type': 'type2',
            })
            message = 'You Measured ' + str(self.sh_measure) + ' mm and it should be between ' + str(
                self.sh_quality_point_id.sh_unit_from) + ' and ' + str(self.sh_quality_point_id.sh_unit_to) + ' mm.'

        if self.sh_measure >= self.sh_quality_point_id.sh_unit_from and self.sh_measure <= self.sh_quality_point_id.sh_unit_to and self.workorder_id:
            self.env['sh.mrp.quality.check'].sudo().create({
                'product_id': self.product_id.id,
                'sh_picking': self.picking_id.id,
                'sh_control_point': self.sh_quality_point_id.name,
                'control_point_id': self.sh_quality_point_id.id,
                'sh_date': fields.Datetime.now(),
                'sh_norm': self.sh_measure,
                'sh_workorder_id': self._context.get('default_workorder_id'),
                'state': 'pass',
                'qc_type': 'type2',

            })
        elif self.workorder_id:
            self.env['sh.mrp.quality.check'].sudo().create({
                'product_id': self.product_id.id,
                'sh_picking': self.picking_id.id,
                'sh_control_point': self.sh_quality_point_id.name,
                'control_point_id': self.sh_quality_point_id.id,
                'sh_date': fields.Datetime.now(),
                'sh_norm': self.sh_measure,
                'sh_workorder_id': self._context.get('default_workorder_id'),
                'state': 'fail',
                'qc_type': 'type2',
            })
        if self.mrp_id:
            lines = self.env['sh.mrp.quality.check'].search([('control_point_id', 'not in', self.__class__.ids_list),
                                                             ('sh_mrp', '=', self.mrp_id.id),
                                                             ('state', '=', 'fail'),
                                                             ('product_id', '=', self.product_id.id,
                                                              ),
                                                             ])

            if len(lines) > 0:
                for i in lines:
                    if i.control_point_id.number_of_test >= self._context.get('default_count') \
                            or i.control_point_id.number_of_test == 0:
                        return {
                            'name': 'Quality Check',
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'sh.quality.global.wizard.fail',
                            'context': {'default_mrp_id': self.mrp_id.id,
                                        'default_point_id': i.control_point_id.id, 'default_count':
                                            self._context.get('default_count')},
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
                    'res_model': 'sh.quality.global.wizard.fail',
                    'type': 'ir.actions.act_window_close',
                }
        if self.workorder_id:
            lines = self.env['sh.mrp.quality.check'].search([('control_point_id', 'not in', self.__class__.ids_list),
                                                             ('product_id', '=', self.product_id.id,
                                                              ),
                                                             ('sh_workorder_id', '=', self.workorder_id.id),
                                                             ('state', '=', 'fail'),

                                                             ])
            if len(lines) > 0:
                for i in lines:
                    if i.control_point_id.number_of_test >= self._context.get('default_count')\
                            or i.control_point_id.number_of_test == 0:
                        return {
                            'name': 'Quality Check',
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'sh.quality.global.wizard.fail',
                            'context': {'default_workorder_id': self.workorder_id.id,
                                        'default_point_id': i.control_point_id.id,
                                        'default_transfer': i.control_point_id.operation.id,
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
                    'res_model': 'sh.quality.global.wizard.fail',
                    'type': 'ir.actions.act_window_close',
                }

    def action_fail(self):
        if self.type == 'type1' and self.mrp_id:
            self.env['sh.mrp.quality.check'].create({
                'product_id': self.product_id.id,
                # 'sh_workorder_id': self.workorder_id.id,
                'sh_control_point': self.sh_quality_point_id.name,
                'control_point_id': self.sh_quality_point_id.id,
                'sh_date': fields.Datetime.now(),
                'sh_norm': 0.0,
                'sh_mrp': self._context.get('default_mrp_id'),
                'state': 'fail',
                'qc_type': 'type1'
            })
        elif self.type == 'type3' and self.mrp_id:
            self.env['sh.mrp.quality.check'].sudo().create({
                'product_id': self.product_id.id,
                'sh_workorder_id': self.workorder_id.id,
                'sh_control_point': self.sh_quality_point_id.name,
                'control_point_id': self.sh_quality_point_id.id,
                'sh_date': fields.Datetime.now(),
                'sh_mrp': self._context.get('default_mrp_id'),
                'sh_norm': 0.0,
                'state': 'fail',
                'qc_type': 'type3',
                'attachment_ids': [(6, 0, self.attachment_ids.ids)]
            })
            if self.attachment_ids:
                self.picking_id.write(
                    {'attachment_ids': [(6, 0, self.attachment_ids.ids)]})

        elif self.type == 'type4' and self.mrp_id:
            self.env['sh.mrp.quality.check'].sudo().create({
                'product_id': self.product_id.id,
                'sh_picking': self.picking_id.id,
                'sh_control_point': self.sh_quality_point_id.name,
                'control_point_id': self.sh_quality_point_id.id,
                'sh_date': fields.Datetime.now(),
                'sh_norm': 0.0,
                'state': 'fail',
                'qc_type': 'type4',
                'sh_mrp': self._context.get('default_mrp_id'),
                'text_message': self.text_message,
                'company_id': self.env.user.company_id.id,
            })

        if self.type == 'type1' and self.workorder_id:
            self.env['sh.mrp.quality.check'].create({
                'product_id': self.product_id.id,
                # 'sh_workorder_id': self.workorder_id.id,
                'sh_control_point': self.sh_quality_point_id.name,
                'control_point_id': self.sh_quality_point_id.id,
                'sh_date': fields.Datetime.now(),
                'sh_norm': 0.0,
                'sh_workorder_id': self._context.get('default_workorder_id'),
                'state': 'fail',
                'qc_type': 'type1'
            })

        elif self.type == 'type3' and self.workorder_id:
            self.env['sh.mrp.quality.check'].sudo().create({
                'product_id': self.product_id.id,
                'sh_workorder_id': self.workorder_id.id,
                'sh_control_point': self.sh_quality_point_id.name,
                'control_point_id': self.sh_quality_point_id.id,
                'sh_date': fields.Datetime.now(),
                'sh_workorder_id': self._context.get('default_workorder_id'),
                'sh_norm': 0.0,
                'state': 'fail',
                'qc_type': 'type3',
                'attachment_ids': [(6, 0, self.attachment_ids.ids)]
            })
        elif self.type == 'type4' and self.workorder_id:
            self.env['sh.mrp.quality.check'].sudo().create({
                'product_id': self.product_id.id,
                'sh_picking': self.picking_id.id,
                'sh_control_point': self.sh_quality_point_id.name,
                'control_point_id': self.sh_quality_point_id.id,
                'sh_date': fields.Datetime.now(),
                'sh_norm': 0.0,
                'state': 'fail',
                'qc_type': 'type4',
                'sh_workorder_id': self._context.get('default_workorder_id'),
                'text_message': self.text_message,
                'company_id': self.env.user.company_id.id,
            })

        if self.mrp_id:
            lines = self.env['sh.mrp.quality.check'].search([('control_point_id', 'not in', self.__class__.ids_list),
                                                             ('sh_mrp', '=', self.mrp_id.id),
                                                             ('state', '=', 'fail'),
                                                             ('product_id', '=', self.product_id.id,
                                                              ),
                                                             ])

            if len(lines) > 0:
                for i in lines:
                    if i.control_point_id.number_of_test >= self._context.get('default_count') or\
                            i.control_point_id.number_of_test == 0:
                        return {
                            'name': 'Quality Check',
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'sh.quality.global.wizard.fail',
                            'context': {'default_mrp_id': self.mrp_id.id,
                                        'default_point_id': i.control_point_id.id, 'default_count':
                                            self._context.get('default_count')},
                            'target': 'new',
                        }
                    else:
                        self.__class__.ids_list.clear()
                        return {
                            'res_model': 'sh.quality.global.wizard.fail',
                            'type': 'ir.actions.act_window_close',
                        }

            else:

                self.__class__.ids_list.clear()
                return {
                    'res_model': 'sh.quality.global.wizard.fail',
                    'type': 'ir.actions.act_window_close',
                }
        if self.workorder_id:
            lines = self.env['sh.mrp.quality.check'].search([('control_point_id', 'not in', self.__class__.ids_list),
                                                             ('product_id', '=', self.product_id.id,
                                                              ),
                                                             ('sh_workorder_id', '=', self.workorder_id.id),
                                                             ('state', '=', 'fail'),
                                                             ])
            if len(lines) > 0:
                for i in lines:
                    if i.control_point_id.number_of_test >= self._context.get('default_count')\
                            or i.control_point_id.number_of_test == 0:
                        return {
                            'name': 'Quality Check',
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'sh.quality.global.wizard.fail',
                            'context': {'default_workorder_id': self.workorder_id.id,
                                        'default_point_id': i.control_point_id.id,
                                        'default_transfer': i.control_point_id.operation.id,
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
                self.__class__.ids_list.clear()
                return {
                    'res_model': 'sh.quality.global.wizard.fail',
                    'type': 'ir.actions.act_window_close',
                }
