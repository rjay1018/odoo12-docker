# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _


class WorkOrder(models.Model):
    _inherit = 'mrp.workorder'

    sh_mrp_workorder_quality_check_ids = fields.One2many(
        'sh.mrp.quality.check', 'sh_workorder_id', string="Mrp WorkOrder Quality Checks")

    sh_mrp_workorder_quality_alert_ids = fields.One2many(
        'sh.mrp.quality.alert', 'workorder_id', string="Mrp Quality Checks")

    sh_mrp_workorder_pass_fail_ids = fields.One2many(
        'sh.mrp.pass.fail', 'workorder_id', string="Mrp Pass Fail Quality Checks")
    sh_mrp_workorder_pics_ids = fields.One2many(
        'sh.mrp.pics', 'workorder_id', string="Mrp pics Quality Checks")

    sh_mrp_workorder_measurement_ids = fields.One2many(
        'sh.mrp.measurement', 'workorder_id', string="Workorder measurement Quality Checks")
    sh_mrp_workorder_qc_measurement_ids = fields.One2many(
        'sh.mrp.qc.measurement', 'workorder_id', string="Workorder QC measurement Quality Checks")

    qc_count = fields.Integer('Quality Checks', compute='_compute_get_qc_count')
    qc_alert_count = fields.Integer(
        'Quality Alerts', compute='_compute_get_qc_alert_count')

    sh_workorder_quality_point_id = fields.Many2one(
        related='production_id.sh_mrp_quality_point_id', string='Quality Control Point')

    need_qc = fields.Boolean(
        "Need QC", related='production_id.need_qc', store=True)

    pending_qc = fields.Boolean(
        "Pending QC", compute='_compute_check_qc', search='search_workorder_pending_qc')

    qc_fail = fields.Boolean(
        "QC Fail", compute='_compute_check_qc', search='search_workorder_fail_qc')
    qc_pass = fields.Boolean(
        "QC Pass", compute='_compute_check_qc', search='search_workorder_pass_qc')

    attachment_ids = fields.Many2many(
        'ir.attachment', string="QC Pictures", copy=False)

    partner_id = fields.Many2one(
        related='production_id.partner_id', string='Contact')

    is_mandatory = fields.Boolean(
        "QC Mandatory", compute='_compute_check_qc_mandatory')

    count = fields.Integer(default=0)
    qc_total_count = fields.Integer(compute='_get_qc_total_count')
    qc_button_hide = fields.Boolean(compute='_get_qc_hide')
    qc_count = fields.Integer('Quality Checks', compute='_compute_get_qc_count')

    @api.depends('count')
    def _get_qc_total_count(self):
        for rec in self:
            rec.qc_total_count = 0
            qc = self.env['sh.mrp.quality.check'].sudo().search(
                [('sh_workorder_id', '=', rec.id)])
            list1 = []
            list2 = []
            for i in qc:
                if i.control_point_id.id not in list2:
                    list2.append(i.control_point_id.id)
                    list1.append(i.control_point_id.number_of_test)
            if list1:
                rec.qc_total_count = max(list1)

    @api.depends('count')
    def _get_qc_hide(self):
        for rec in self:
            qc = self.env['sh.mrp.quality.check'].sudo().search(
                [('sh_workorder_id', '=', rec.id)])
            count = 0
            list1 = []
            list2 = []
            for i in qc:
                list1.append(i.control_point_id.id)
                if i.control_point_id.number_of_test == self.qc_total_count and i.control_point_id.id \
                        in list1:
                    count += 1
                elif i.control_point_id.number_of_test == 0 and \
                        i.control_point_id.id not in [l.control_point_id.id for l in
                                                      qc.filtered(lambda i: i.state == 'pass')]:
                    rec.qc_button_hide = False
                    break

                elif i.control_point_id.number_of_test == 0 and \
                        i.control_point_id.id in [l.control_point_id.id for l in
                                                  qc.filtered(lambda i: i.state == 'pass')]:
                    rec.qc_button_hide = True

            if count == 0:
                rec.qc_button_hide = False
                break
            if rec.qc_total_count > count:
                rec.qc_button_hide = False
            elif rec.qc_total_count <= count:
                rec.qc_button_hide = True
                break

    def search_workorder_pending_qc(self, operator, value):
        rec_ids = []
        for rec_id in self.search([]):
            if rec_id.pending_qc:
                rec_ids.append(rec_id.id)
        return [('id', 'in', rec_ids)]

    def search_workorder_fail_qc(self, operator, value):
        rec_ids = []
        for rec_id in self.search([]):
            if rec_id.qc_fail:
                rec_ids.append(rec_id.id)
        return [('id', 'in', rec_ids)]

    def search_workorder_pass_qc(self, operator, value):
        rec_ids = []
        for rec_id in self.search([]):
            if rec_id.qc_pass:
                rec_ids.append(rec_id.id)
        return [('id', 'in', rec_ids)]

    def _compute_check_qc(self):
        if self:
            for rec in self:
                rec.qc_pass = False
                rec.qc_fail = False
                rec.pending_qc = False
                if rec.need_qc == True:
                    rec.pending_qc = True

                last_quality_check = self.env['sh.mrp.quality.check'].sudo().search(
                    [('product_id', '=', rec.product_id.id), ('sh_workorder_id', '=', rec.id)], order='create_date desc')

                if last_quality_check:
                    for qc in last_quality_check:

                        if qc.state == 'fail' and qc.control_point_id.id not in \
                                [i.control_point_id.id for i in rec.sh_mrp_workorder_quality_check_ids.filtered(lambda i: i.state == 'pass')]:

                            rec.qc_fail = True
                            rec.qc_pass = False
                            rec.pending_qc = False
                            rec.need_qc = False
                            break

                        else:
                            rec.qc_pass = True
                            rec.qc_fail = False
                            rec.pending_qc = False
                            rec.need_qc = False

    def _compute_check_qc_mandatory(self):
        if self:
            for rec in self:
                rec.is_mandatory = False
                if rec.sh_workorder_quality_point_id and rec.sh_workorder_quality_point_id.is_mandatory:
                    rec.is_mandatory = True

    def workorder_quality_point(self):
        if self.sh_workorder_quality_point_id:
            quality_point_id = self.env['sh.qc.point'].sudo().search([
                ('product_id', '=', self.product_id.id),
                ('operation.id', '=', self.production_id.picking_type_id.id),
                '|', ('team.user_ids.id', 'in', [self.env.uid]),
                ('team', '=', False)],
                order='create_date desc')

            if len(self.sh_mrp_workorder_quality_check_ids) >= self.sh_workorder_quality_point_id.number_of_test and self.sh_workorder_quality_point_id.number_of_test != 0\
                    and not self.sh_mrp_workorder_quality_check_ids.filtered(lambda i: i.state == 'fail'):

                message = 'You Maximum number of allowed Test is Over Now'

            elif self.sh_mrp_workorder_quality_check_ids.filtered(lambda i: i.state == 'fail'):
                self.count +=1
                for i in self.sh_mrp_workorder_quality_check_ids.filtered(lambda i: i.state == 'fail'):
                    if i.control_point_id.id in [i.control_point_id.id for i in self.sh_mrp_workorder_quality_check_ids.filtered(lambda i: i.state =='pass')]:
                        message = "dsfmsdkfm"
                    elif i.control_point_id.number_of_test >= self.count or i.control_point_id.number_of_test == 0:
                        return {
                            'name': 'NO. of Allowed Quality Checks',
                            'type': 'ir.actions.act_window',
                            'view_type': 'form',
                            'view_mode': 'form',
                            'res_model': 'sh.quality.global.wizard.fail',
                            'context': {'default_workorder_id': self.id, 'default_point_id': i.control_point_id.id,
                                        'default_transfer': i.control_point_id.operation.id,
                                        'default_count': self.count},
                            'target': 'new',
                        }
            else:
                for i in quality_point_id:
                    if i.routing_workcenter_ids.filtered(lambda i: i.operation_name == self.name
                                                                           and i.allow_quality_check == True):
                        rec = i.routing_workcenter_ids.filtered(lambda i: i.operation_name == self.name
                                                                           and i.allow_quality_check == True)
                        if rec:
                            self.count += 1
                            return {
                                'name': 'NO. of Allowed Quality Checks',
                                'type': 'ir.actions.act_window',
                                'view_type': 'form',
                                'view_mode': 'form',
                                'res_model': 'sh.quality.global.wizard',
                                'context': {'default_workorder_id': self.id,
                                            'default_point_id': rec[0].qc_point_id.id,
                                            'default_transfer': rec[0].qc_point_id.operation.id,
                                            'default_count': self.count},
                                'target': 'new',
                                }

    def action_quality_alert(self):
        line_ids = []
        if self:
            vals = {
                'product_id': self.product_id.id,
                'partner_id': self.partner_id.id,
            }
            line_ids.append((0, 0, vals))
        return {
            'name': 'Quality Alert',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sh.mrp.qc.alert',
            'context': {'default_alert_ids': line_ids},
            'target': 'new',
        }

    def open_quality_check(self):
        po = self.env['sh.mrp.quality.check'].sudo().search(
            [('sh_workorder_id', '=', self.id)])
        action = self.env.ref(
            'sh_inventory_mrp_qc.mrp_quality_check_action').read()[0]
        action['context'] = {
            'domain': [('id', 'in', po.ids)]

        }
        action['domain'] = [('id', 'in', po.ids)]
        return action

    def open_quality_alert(self):
        alert_ids = self.env['sh.mrp.quality.alert'].sudo().search(
            [('workorder_id', '=', self.id)])
        action = self.env.ref(
            'sh_inventory_mrp_qc.mrp_quality_alert_action').read()[0]
        action['context'] = {
            'domain': [('id', 'in', alert_ids.ids)]
        }
        action['domain'] = [('id', 'in', alert_ids.ids)]
        return action

    def _compute_get_qc_count(self):
        if self:
            for rec in self:
                rec.qc_count = 0
                qc = self.env['sh.mrp.quality.check'].sudo().search(
                    [('sh_workorder_id', '=', rec.id)])
                rec.qc_count = len(qc.ids)

    def _compute_get_qc_alert_count(self):
        if self:
            for rec in self:
                rec.qc_alert_count = 0
                qlarts = self.env['sh.mrp.quality.alert'].sudo().search(
                    [('workorder_id', '=', rec.id)])
                rec.qc_alert_count = len(qlarts.ids)
