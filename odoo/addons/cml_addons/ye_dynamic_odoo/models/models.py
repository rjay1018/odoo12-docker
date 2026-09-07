from odoo.models import BaseModel, AbstractModel
from odoo import api
from lxml import etree

_load_views = AbstractModel.load_views
_fields_view_get = AbstractModel.fields_view_get

@api.model
def load_views(self, views, options=None):
    res = _load_views(self, views, options=options)
    return res

@api.model
def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    res = _fields_view_get(self, view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    res['fieldsGet'] = self.env[self._name].fields_get()
    if 'odo.studio' in self.env.registry.models and res and 'view_id' in res:
        ui_view = self.env['ir.ui.view']
        model_view = "odo.studio.sub_view" if self.env.context.get("useSubView", False) else 'odo.studio'
        view_studio = self.env[model_view].search([['view_id', '=', res['view_id']]])
        if len(view_studio):
            res['arch'] = view_studio[0].xml
        for fieldName in res['fieldsGet']:
            if fieldName not in res['fields']:
                field_appear = res['fieldsGet'][fieldName]
                if field_appear['type'] in ["one2many", "many2many"]:
                    field_appear['views'] = {}
                res['fields'][fieldName] = field_appear
        sub_view_exist = self.env['odo.studio.sub_view'].search([['parent_view_id', '=', res.get('view_id', False)]])
        for sub_view in sub_view_exist:
            field_name = sub_view.field_name
            view_type = sub_view.view_type
            views = res['fields'][field_name]['views']
            sub_view_model = res['fields'][field_name]['relation']
            if type(views) is dict:
                if view_type not in views:
                    views[view_type] = {}
                view_process = ui_view.postprocess_and_fields(sub_view_model, etree.fromstring(sub_view.xml),
                                                              sub_view.view_id.id)
                views[view_type]['arch'] = sub_view.xml
                views[view_type]['fields'] = view_process[1]

    return res


AbstractModel.load_views = load_views
AbstractModel.fields_view_get = fields_view_get
