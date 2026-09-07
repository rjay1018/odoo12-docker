from odoo import fields, models, api


class UomExtended(models.Model):
    _inherit = "uom.uom"

    content = fields.Char(
        String='Content'
    )

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        domain = args + ['|', ('name', operator, name), ('content', operator, name)]
        return super(UomExtended, self).search(domain, limit=limit).name_get()
