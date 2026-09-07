from odoo import models, api, fields


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    model_id = fields.Many2one(string="Model", comodel_name="ir.model")

    @api.model_create_multi
    def create(self, values):
        res = super(IrUiMenu, self).create(values)
        if res.model_id and not res.action:
            model_action = self.env['ir.actions.act_window'].search([('res_model', '=', res.model_id.model)])
            # , ('view_id', '!=', False)])
            if len(model_action):
                has_view = model_action.filtered(lambda x: x.view_id != False)
                if len(has_view):
                    model_action = has_view
                res.write({'action': '%s,%s' % ('ir.actions.act_window', model_action[0].id)})

        return res

    @api.model
    def get_form_view_id(self, view_type=None):
        if view_type == 'edit':
            return self.env.ref('ye_dynamic_odoo.edit_menu_form_view').id
        if view_type == "create":
            return self.env.ref('ye_dynamic_odoo.create_menu_form_view').id

    @api.model
    def prepare_data(self, menu):
        parent_id = menu['parent_id']
        return {
            'name': menu['name'],
            'sequence': menu['sequence'],
            'parent_id': parent_id[0] if parent_id else parent_id,
        }

    @api.model
    def update_menu(self, data):
        data_delete = data.get('_delete', False)
        if data_delete:
            self.browse(data_delete).unlink()
        new_ids = {}
        for menu in data['_new']:
            new_ids[menu['id']] = self.create(self.prepare_data(menu)).id
        while len(data['_newAll']) > 0:
            list_create = []
            list_wait = []
            for menu in data['_newAll']:
                list_create.append(menu) if menu['parent_id'][0] in new_ids else list_wait.append(menu)
            data['_newAll'] = list_wait
            for menu in list_create:
                values = self.prepare_data(menu)
                values['parent_id'] = new_ids[menu['parent_id'][0]]
                new_ids[menu['id']] = self.create(values).id
        for menu in data['_parent']:
            values = self.prepare_data(menu)
            values['parent_id'] = new_ids[menu["parent_id"][0]]
            self.browse(menu["id"]).write(values)
        for menu in data['_old']:
            values = self.prepare_data(menu)
            self.browse(menu["id"]).write(values)
        return True



IrUiMenu()
