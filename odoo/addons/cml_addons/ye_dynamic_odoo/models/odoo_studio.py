from odoo import fields, models, api


class ODOOStudio(models.Model):
    _name = "odo.studio"

    xml = fields.Text(string="Xml")
    view_id = fields.Many2one(string="View id", comodel_name="ir.ui.view")
    new_fields = fields.Many2many('ir.model.fields', string="New Fields", copy=False)

    @api.model
    def create_new_view(self, values):
        view_id = self.env['ir.ui.view'].create(values.get("data", {}))
        values_action_view = {'sequence': 100, 'view_id': view_id.id,
                              'act_window_id': values.get('action_id', False), 'view_mode': values.get('view_mode', False)}
        self.env['ir.actions.act_window.view'].create(values_action_view)
        return view_id

    @api.model
    def store_view(self, values):
        views_exist = self.search([['view_id', '=', values.get('view_id', False)]], limit=1)
        new_fields = values.get("new_fields", False)
        model_name = values.get("model_name", False)
        if model_name and new_fields and len(new_fields):
            model_obj = self.env['ir.model'].search([('model', '=', model_name)])
            [new_field.update({'model_id': model_obj.id, 'state': 'manual'}) for new_field in new_fields]
            values['new_fields'] = [(0, 0, new_field) for new_field in new_fields]
        if len(views_exist) > 0:
            views_exist.write({'xml': values['xml'], 'new_fields': values['new_fields']})
        else:
            self.create(values)
        return True

    @api.model
    def undo_view(self, values):
        self.env['odo.studio.sub_view'].search([['parent_view_id', '=', values.get('view_id', False)]]).unlink()
        return self.search([['view_id', '=', values.get('view_id', False)]]).unlink()

    @api.model
    def load_field_get(self, model_name):
        return self.env[model_name].fields_get()


ODOOStudio()


class OdoStudioSubView(models.Model):
    _name = "odo.studio.sub_view"

    xml = fields.Text(string="Xml")
    view_key = fields.Char(string="View Key") # sale_order_field_order_line_list
    view_id = fields.Many2one(string="View id", comodel_name="ir.ui.view")
    parent_view_id = fields.Many2one(string="Parent View Id", comodel_name="ir.ui.view")
    parent_model_name = fields.Char(string="Parent Model Name")
    field_name = fields.Char(string="Field Name")
    view_type = fields.Selection([('tree', 'Tree'), ('form', 'Form')], string="View Type")
    new_fields = fields.Many2many('ir.model.fields', string="New Fields", copy=False)

    @api.model
    def store_view(self, values):
        views_exist = self.search([['view_key', '=', values.get('view_key', False)]])
        new_fields = values.get("new_fields", False)
        model_name = values.get("model_name", False)
        if model_name and new_fields and len(new_fields):
            model_obj = self.env['ir.model'].search([('model', '=', model_name)])
            [new_field.update({'model_id': model_obj.id, 'state': 'manual'}) for new_field in new_fields]
            values['new_fields'] = [(0, 0, new_field) for new_field in new_fields]
        if len(views_exist) > 0:
            views_exist.write(values)
        else:
            self.create(values)
        return True

    @api.model
    def undo_view(self, values):
        return self.search([['view_id', '=', values.get('view_id', False)], ['field_name', '=', values.get('field_name', False)],
                            ['parent_view_id', '=', values.get('parent_view_id', False)]]).unlink()

OdoStudioSubView()
