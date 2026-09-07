# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sh_quality_check_ids = fields.Many2many(
        'sh.quality.check', string="Quality Checks", compute='_get_quality_check_ids')
    sh_quality_alert_ids = fields.Many2many(
        'sh.quality.alert', string="Quality Alert", compute='_get_quality_alert_ids')
    qc_count = fields.Integer('Quality Checks', compute='_get_qc_count')
    qc_alert_count = fields.Integer(
        'Quality Alerts', compute='_get_qc_alert_count')
    need_qc = fields.Boolean(
        "Need QC",
        # compute="_check_need_qc",
        compute='check_need_qc_compute',
        search='search_need_qc')
    qc_fail = fields.Boolean(
        "QC Fail",
        # compute="_check_need_qc",
        compute='check_qc_fail_pass_compute',
        search='search_fail_qc')
    qc_pass = fields.Boolean(
        "QC Pass",
        # compute="_check_need_qc",
        compute='check_qc_fail_pass_compute',
        search='search_pass_qc')
    full_pass = fields.Boolean(
        "Full Pass",
        # compute="_check_need_qc",
        compute='check_full_pass_compute',
        search='search_full_pass_qc')
    is_mandatory = fields.Boolean(
        "QC Mandatory", compute='_check_qc_mandatory', search='search_mandatory_qc')
    attachment_ids = fields.Many2many(
        'ir.attachment', string="QC Pictures", copy=False)
    # qc_total_count = fields.Integer(compute='_get_qc_total_count')
    qc_button_hide = fields.Boolean(default=False,
                                    compute='check_qc_button_hide_compute')



    def check_need_qc_compute(self):
        if self:
            count = 0
            for rec in self:
                rec.need_qc = False
                if rec.move_ids_without_package:
                    len_move_id = 0
                    for move in rec.move_ids_without_package.filtered(lambda x: x.sh_quality_point_id):
                        quality_point_id = move.sh_quality_point_id
                        if quality_point_id:
                            rec.need_qc = True
                            if move.sh_last_qc_state == 'fail':
                                len_move_id += 1


    def check_qc_fail_pass_compute(self):
        if self:
            count = 0
            for rec in self:
                rec.qc_fail = False
                rec.qc_pass = False
                if rec.move_ids_without_package:
                    len_move_id = 0

                    for move in rec.move_ids_without_package.filtered(lambda x: x.sh_quality_point_id):
                        quality_point_id = move.sh_quality_point_id

                        if quality_point_id:
                            rec.need_qc = True
                            if move.sh_last_qc_state == 'fail':
                                len_move_id += 1

                    if len_move_id > 0:
                        if len(rec.sh_quality_check_ids.ids) > 0:
                            rec.qc_fail = True
                            rec.qc_pass = False
                    elif len_move_id == 0:
                        if len(rec.sh_quality_check_ids.ids) > 0:
                            rec.qc_fail = False
                            rec.qc_pass = True
                            rec.qc_button_hide = False



    def check_full_pass_compute(self):
        if self:
            count = 0
            for rec in self:
                rec.full_pass = False


    def check_qc_button_hide_compute(self):
        if self:
            count = 0
            for rec in self:
                list_total = []
                if list_total:
                    for re in rec.move_ids_without_package:
                        if re.count != 0:
                            if max(list_total) == re.count:
                                rec.qc_button_hide = True
                    for i in rec.sh_quality_check_ids:
                        if i.control_point_id.number_of_test == 0 and i.control_point_id.id not in [
                            j.control_point_id.id for j in
                            rec.sh_quality_check_ids.filtered(lambda k: k.state == 'pass')]:
                            rec.qc_button_hide = False
                        elif i.control_point_id.number_of_test == 0 and i.control_point_id.id in [j.control_point_id.id
                                                                                                  for j in
                                                                                                  rec.sh_quality_check_ids.filtered(
                                                                                                      lambda
                                                                                                          k: k.state == 'pass')]:
                            rec.qc_button_hide = True


    def search_need_qc(self, operator, value):
        rec_ids = []
        for rec_id in self.search([]):
            if rec_id.need_qc and not rec_id.qc_fail and not rec_id.qc_pass and not rec_id.full_pass:
                rec_ids.append(rec_id.id)
        return [('id', 'in', rec_ids)]

    def search_fail_qc(self, operator, value):
        rec_ids = []
        for rec_id in self.search([]):
            if rec_id.qc_fail:
                rec_ids.append(rec_id.id)
        return [('id', 'in', rec_ids)]

    def search_pass_qc(self, operator, value):
        rec_ids = []
        for rec_id in self.search([]):
            if rec_id.qc_pass and rec_id.need_qc:
                rec_ids.append(rec_id.id)
        return [('id', 'in', rec_ids)]

    def search_mandatory_qc(self, operator, value):
        rec_ids = []
        for rec_id in self.search([]):
            if rec_id.is_mandatory:
                rec_ids.append(rec_id.id)
        return [('id', 'in', rec_ids)]

    def search_full_pass_qc(self, operator, value):
        rec_ids = []
        for rec_id in self.search([]):
            if rec_id.full_pass and rec_id.need_qc:
                rec_ids.append(rec_id.id)
        return [('id', 'in', rec_ids)]

    def _check_qc_mandatory(self):
        if self:
            for rec in self:
                rec.is_mandatory = False
                if rec.move_ids_without_package:
                    for move in rec.move_ids_without_package:
                        if move.sh_quality_point_id:
                            self.env.cr.execute(
                                """
                                select point.is_mandatory from sh_qc_point as point FULL OUTER JOIN sh_qc_team as
                                team ON point.team = team.id FULL OUTER JOIN res_users_sh_qc_team_rel as rel ON rel.sh_qc_team_id =
                                team.id where rel.res_users_id = %s and point.product_id = %s and point.operation = %s
                                ORDER BY point.create_date DESC LIMIT 1;
                                """ % (self.env.uid, move.product_id.id, move.picking_id.picking_type_id.id)
                            )
                            data = self.env.cr.fetchall()
                            if data and data[0] and data[0][0]:
                                #                         quality_point_id = self.env['sh.qc.point'].sudo().search([('product_id', '=', move.product_id.id),
                                #                                                                                   ('operation', '=', move.picking_id.picking_type_id.id),
                                #                                                                   '|', ('team.user_ids.id', 'in', [self.env.uid]), ('team', '=', False)
                                #                                                                   ], limit=1, order='create_date desc')
                                #
                                #                         if quality_point_id and quality_point_id.is_mandatory:
                                rec.is_mandatory = True

    # @api.depends('move_ids_without_package')
    # def _check_need_qc(self):
    #     if self:
    #
    #         count = 0
    #         for rec in self:
    #             list_total = []
    #             for i in rec.move_ids_without_package:
    #                 res = self.env['sh.qc.point'].search([('product_id', '=', i.product_id.id)])
    #                 list_qc = []
    #                 for r in res:
    #                     list_qc.append(r.number_of_test)
    #                 if list_qc:
    #                     max_qc = max(list_qc)
    #                     list_total.append(max_qc)
    #             if list_total:
    #                 for re in rec.move_ids_without_package:
    #                     if re.count != 0:
    #                         if max(list_total) == re.count:
    #                             rec.qc_button_hide = True
    #             rec.qc_pass = False
    #             rec.qc_fail = False
    #             rec.need_qc = False
    #             rec.full_pass = False
    #
    #             if rec.move_ids_without_package:
    #                 len_move_id = 0
    #
    #                 for move in rec.move_ids_without_package.filtered(lambda x: x.sh_quality_point_id):
    #                     quality_point_id = move.sh_quality_point_id
    #
    #                     if quality_point_id:
    #                         rec.need_qc = True
    #                         if move.sh_last_qc_state == 'fail':
    #                             len_move_id += 1
    #                 if len_move_id > 0:
    #                     if len(rec.sh_quality_check_ids.ids) > 0:
    #                         rec.qc_fail = True
    #                         rec.qc_pass = False
    #                 elif len_move_id == 0:
    #                     if len(rec.sh_quality_check_ids.ids) > 0:
    #                         rec.qc_fail = False
    #                         rec.qc_pass = True
    #                         rec.qc_button_hide = True
    #                 for i in rec.sh_quality_check_ids:
    #                     if i.control_point_id.number_of_test == 0 and i.control_point_id.id not in [
    #                         j.control_point_id.id for j in
    #                         rec.sh_quality_check_ids.filtered(lambda k: k.state == 'pass')]:
    #                         rec.qc_button_hide = False
    #                     elif i.control_point_id.number_of_test == 0 and i.control_point_id.id in [j.control_point_id.id
    #                                                                                               for j in
    #                                                                                               rec.sh_quality_check_ids.filtered(
    #                                                                                                   lambda
    #                                                                                                       k: k.state == 'pass')]:
    #                         rec.qc_button_hide = True

    def _get_qc_count(self):
        if self:
            for rec in self:
                rec.qc_count = 0

                self.env.cr.execute(
                    """
                    select count(*) from sh_quality_check as qc where sh_picking= %s ;
                    """ % (rec.id)
                )
                qc_data = self.env.cr.fetchall()
                if qc_data and qc_data[0] and qc_data[0][0]:
                    rec.qc_count = qc_data[0][0]

    #                 qc = self.env['sh.quality.check'].search(
    #                     [('sh_picking', '=', rec.id)])
    #                 rec.qc_count = len(qc.ids)

    def _get_qc_alert_count(self):
        if self:
            for rec in self:
                rec.qc_alert_count = 0
                self.env.cr.execute(
                    """
                    select count(*) from sh_quality_alert as qc where piking_id= %s ;
                    """ % (rec.id)
                )
                qc_data = self.env.cr.fetchall()
                if qc_data and qc_data[0] and qc_data[0][0]:
                    rec.qc_alert_count = qc_data[0][0]

    #                 qlarts = self.env['sh.quality.alert'].search(
    #                     [('piking_id', '=', rec.id)])
    #                 rec.qc_alert_count = len(qlarts.ids)

    def _get_quality_check_ids(self):
        if self:
            for rec in self:
                rec.sh_quality_check_ids = False
                if rec.id:
                    quality_check_ids = []
                    self.env.cr.execute(
                        """
                        select qc.id from sh_quality_check as qc where sh_picking= %s ;
                        """ % (rec.id,)
                    )
                    qc_data = self.env.cr.fetchall()
                    for qc in qc_data:
                        quality_check_ids.append(qc[0])

                    rec.sh_quality_check_ids = [(6, 0, quality_check_ids)]

    def _get_quality_alert_ids(self):
        if self:
            for rec in self:
                rec.sh_quality_alert_ids = False

                if rec.id:
                    quality_alert_ids = []
                    self.env.cr.execute(
                        """
                        select qc.id from sh_quality_alert as qc where piking_id= %s ;
                        """ % (rec.id,)
                    )
                    qc_data = self.env.cr.fetchall()
                    for qc in qc_data:
                        quality_alert_ids.append(qc[0])

                    rec.sh_quality_alert_ids = [(6, 0, quality_alert_ids)]

    def quality_point(self):
        if self:
            # line= self.move_ids_without_package
            lines = self.move_ids_without_package.filtered(
                lambda x: not x.qc_hide and x.sh_quality_point)
            # and x.sh_quality_point
            if lines:
                need_qc = False
                line_id = False

                for line in lines:
                    self.env.cr.execute(
                        """
                        select point.id from sh_qc_point as point FULL OUTER JOIN sh_qc_team as
                        team ON point.team = team.id FULL OUTER JOIN res_users_sh_qc_team_rel as rel ON rel.sh_qc_team_id =
                        team.id where point.product_id = %s and point.operation = %s
                        ORDER BY point.create_date DESC LIMIT 1;
                        """ % (line.product_id.id, line.picking_id.picking_type_id.id)
                    )
                    # self.env.cr.execute(
                    #     """
                    #     select point.id from sh_qc_point as point FULL OUTER JOIN sh_qc_team as
                    #     team ON point.team = team.id FULL OUTER JOIN res_users_sh_qc_team_rel as rel ON rel.sh_qc_team_id =
                    #     team.id where rel.res_users_id = %s and point.product_id = %s and point.operation = %s
                    #     ORDER BY point.create_date DESC LIMIT 1;
                    #     """ % (self.env.uid, line.product_id.id, line.picking_id.picking_type_id.id)
                    # )
                    data = self.env.cr.fetchall()
                    quality_point_id = False
                    if data and data[0] and data[0][0]:
                        quality_point_id = data[0][0] or False

                        # quality_point_id = self.env['sh.qc.point'].sudo().search([('product_id', '=', line.product_id.id),
                        #                                                         ('operation', '=', line.picking_id.picking_type_id.id),
                        #                                                   # '|', ('team.user_ids.id', 'in', [self.env.uid]), ('team', '=', False)
                        #                                                   ], limit=1, order='create_date desc')
                        # if quality_point_id:
                        #     line.write({'sh_quality_point_id': quality_point_id, 'sh_quality_point': True})
                    if not need_qc and line.number_of_test > 0:
                        line_id = line.id
                        need_qc = True

                    if need_qc and not self.sh_quality_check_ids.filtered(lambda i: i.state == 'fail'):
                        if quality_point_id:
                            line.count += 1

                            return {
                                'name': 'Quality Check',
                                'type': 'ir.actions.act_window',
                                'view_type': 'form',
                                'view_mode': 'form',
                                'res_model': 'sh.stock.move.global.check',
                                'context': {'default_move_id': line_id, "default_transfer": self.picking_type_id.id,
                                            'default_point_id': quality_point_id,
                                            'default_product_id': line.product_id.id,
                                            },
                                'target': 'new',

                            }

                    elif self.sh_quality_check_ids.filtered(lambda i: i.state == 'fail'):

                        for i in self.sh_quality_check_ids.filtered(lambda i: i.state == 'fail'):
                            if i.control_point_id.id in [i.control_point_id.id for i in
                                                         self.sh_quality_check_ids.filtered(lambda i: i.state == 'pass')]:


                                message = "dsfmsdkfm"
                            else:
                                if i.sh_move_id:
                                    if (i.control_point_id.number_of_test > i.sh_move_id.count or i.control_point_id.number_of_test == 0):
                                        for ss in self.move_ids_without_package:
                                            if ss.sh_quality_point:
                                                ss.count += 1


                                        return {
                                            'name': 'NO. of Allowed Quality Checks',
                                            'type': 'ir.actions.act_window',
                                            'view_type': 'form',
                                            'view_mode': 'form',
                                            'res_model': 'stock.move.global.wizard.fail',
                                            'context': {
                                                'default_move_id': i.sh_move_id.id,
                                                "default_transfer": self.picking_type_id.id,
                                                'default_point_id': i.control_point_id.id,
                                                'default_count': i.sh_move_id.count,
                                                'default_product_id': i.product_id.id
                                            },
                                            'target': 'new',
                                        }


    def action_quality_alert(self):
        line_ids = []
        if self.move_ids_without_package:
            for line in self.move_ids_without_package:
                vals = {
                    'product_id': line.product_id.id,
                    'partner_id': self.partner_id.id,
                }
                line_ids.append((0, 0, vals))
        return {
            'name': 'Quality Alert',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sh.qc.alert',
            'context': {'default_alert_ids': line_ids},
            'target': 'new',
        }

    def open_quality_check(self):
        po = self.env['sh.quality.check'].sudo().search(
            [('sh_picking', '=', self.id)])
        action = self.env.ref('sh_inventory_mrp_qc.quality_check_action').read()[0]
        action['context'] = {
            'domain': [('id', 'in', po.ids)]

        }
        action['domain'] = [('id', 'in', po.ids)]
        return action

    def open_quality_alert(self):
        alert_ids = self.env['sh.quality.alert'].sudo().search(
            [('piking_id', '=', self.id)])
        action = self.env.ref('sh_inventory_mrp_qc.quality_alert_action').read()[0]
        action['context'] = {
            'domain': [('id', 'in', alert_ids.ids)]
        }
        action['domain'] = [('id', 'in', alert_ids.ids)]
        return action


class StockMove(models.Model):
    _inherit = 'stock.move'

    sh_quality_point = fields.Boolean('Quality Point')
    sh_quality_point_id = fields.Many2one(
        'sh.qc.point', 'Quality Control Point')
    sh_last_qc_date = fields.Datetime(
        'Last Quality Check Date', compute='_get_last_check_result')
    sh_last_qc_state = fields.Char(
        'Last Quality Check Status', compute='_get_last_check_result')
    number_of_test = fields.Integer(
        "Maximum number of tests allowed.", compute='_get_last_check_result')
    count = fields.Integer('count', default=0, store=True)

    qc_hide = fields.Boolean(default=False, compute='_get_qc_hide')

    @api.depends('count')
    def _get_qc_hide(self):
        for rec in self:
            last_quality_check = rec.picking_id.sh_quality_check_ids.filtered(
                lambda x: x.product_id.id == rec.product_id.id and x.sh_picking.id == rec.picking_id.id)
            for i in last_quality_check:
                if (i.state == 'fail' and i.control_point_id.id not in [i.control_point_id.id for i in
                                                                        rec.picking_id.sh_quality_check_ids.filtered(
                                                                            lambda
                                                                                i: i.state == 'pass')]) and i.control_point_id.number_of_test >= rec.count:
                    rec.picking_id.qc_hide = False
                    rec.qc_hide = False
                    break
                else:
                    rec.picking_id.qc_hide = True
                    rec.qc_hide = True

    @api.model
    def create(self, vals):
        if vals.get('picking_type_id') and vals.get('product_id'):
            quality_point_id = self.env['sh.qc.point'].sudo().search([('product_id', '=', vals.get('product_id')),
                                                                      ('operation', '=', vals.get('picking_type_id')),
                                                                      # '|', ('team.user_ids.id', 'in',
                                                                      #       [self.env.context.get('uid')]),
                                                                      # ('team', '=', False)
                                                                      ], limit=1, order='create_date desc')

            if quality_point_id:
                vals.update({'sh_quality_point': True, 'sh_quality_point_id': quality_point_id.id})
        return super(StockMove, self).create(vals)

    def _get_last_check_result(self):
        if self:
            for rec in self:
                rec.sh_last_qc_date = False
                rec.sh_last_qc_state = ''
                check_count = rec.picking_id.sh_quality_check_ids.filtered(
                    lambda x: x.product_id.id == rec.product_id.id)

                #                 quality_point_id = self.env['sh.qc.point'].sudo().search([('product_id', '=', rec.product_id.id),
                #                                                                                   ('operation', '=', rec.picking_id.picking_type_id.id),
                #                                                                   '|', ('team.user_ids.id', 'in', [self.env.uid]), ('team', '=', False)
                #                                                                   ], limit=1, order='create_date desc')

                quality_point_id = rec.sh_quality_point_id
                number_of_test = 100
                if quality_point_id:
                    if quality_point_id.number_of_test > 0:
                        number_of_test = quality_point_id.number_of_test

                rec.number_of_test = number_of_test - len(check_count)
                #                 last_quality_check = self.env['sh.quality.check'].search(
                #                     [('product_id', '=', rec.product_id.id), ('sh_picking', '=', rec.picking_id.id)], limit=1, order='create_date desc')
                last_quality_check = rec.picking_id.sh_quality_check_ids.filtered(
                    lambda x: x.product_id.id == rec.product_id.id and x.sh_picking.id == rec.picking_id.id).sorted(
                    key=lambda x: x.create_date)
                if last_quality_check:
                    rec.sh_last_qc_date = last_quality_check[0].create_date
                    for i in last_quality_check:
                        if (i.state == 'fail' and i.control_point_id.id not in [i.control_point_id.id for i in
                                                                                rec.picking_id.sh_quality_check_ids.filtered(
                                                                                    lambda i: i.state == 'pass')]) and (
                            i.control_point_id.number_of_test > rec.count or i.control_point_id.number_of_test == 0):
                            rec.sh_last_qc_state = 'fail'
                            break
                        elif i.state == 'fail' and i.control_point_id.id not in [i.control_point_id.id for i in
                                                                                 rec.picking_id.sh_quality_check_ids.filtered(
                                                                                     lambda
                                                                                         i: i.state == 'pass')] and i.control_point_id.number_of_test <= rec.count:
                            rec.sh_last_qc_state = 'fail'
                            break

                        elif i.state == 'pass' or i.control_point_id.id in [i.control_point_id.id for i in
                                                                            rec.picking_id.sh_quality_check_ids.filtered(
                                                                                lambda i: i.state == 'pass')]:
                            rec.sh_last_qc_state = 'pass'

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(StockMove, self).onchange_product_id()
        quality_point_id = self.env['sh.qc.point'].sudo().search(
            [('product_id', '=', self.product_id.id), ('operation', '=', self.picking_id.picking_type_id.id),
             '|', ('team.user_ids.id', 'in', [self.env.uid]), ('team', '=', False)], limit=1, order='create_date desc')
        if quality_point_id:
            self.sh_quality_point = True
            self.sh_quality_point_id = quality_point_id.id
            self.number_of_test = self.sh_quality_point_id.number_of_test
        return res

    def quality_point_line(self):
        quality_point_id = self.env['sh.qc.point'].sudo().search(
            [('product_id', '=', self.product_id.id), ('operation', '=', self.picking_id.picking_type_id.id),
             '|', ('team.user_ids.id', 'in', [self.env.uid]), ('team', '=', False)], limit=1, order='create_date desc')

        if quality_point_id:
            self.write({'sh_quality_point_id': quality_point_id.id, 'sh_quality_point': True})

        if self.sh_quality_point_id.type == 'type2':
            return {
                'name': 'Quality Check',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sh.stock.move.qc.measurement',
                'context': {'default_picking_id': self.picking_id.id},
                'target': 'new',
            }
        elif self.sh_quality_point_id.type == 'type1':
            return {
                'name': 'Quality Check',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sh.stock.move.pass.fail',
                'context': {'default_picking_id': self.picking_id.id},
                'target': 'new',
            }
        elif self.sh_quality_point_id.type == 'type3':
            return {
                'name': 'Quality Check',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sh.stock.move.pics',
                'context': {'default_picking_id': self.picking_id.id},
                'target': 'new',
            }
        elif self.sh_quality_point_id.type == 'type4':
            return {
                'name': 'Quality Check',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sh.stock.move.text',
                'context': {'default_picking_id': self.picking_id.id},
                'target': 'new',
            }

    def quality_alert(self):
        return {
            'name': 'Quality Alerts',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sh.quality.alert',
            'context': {'default_stage_id': self.env.ref('sh_inventory_mrp_qc.alert_stage_0').id,
                        'default_product_id': self.product_id.id, 'default_piking_id': self.picking_id.id,
                        'default_partner_id': self.picking_id.partner_id.id},
            'target': 'current',
        }
