# from odoo import models, fields, api


# class ResConfigSettings(models.TransientModel):
#     _inherit = 'res.config.settings'

#     ot_advance_filing = fields.Boolean('Advance Filing')

#     @api.model
#     def get_values(self):
#         res = super(ResConfigSettings, self).get_values()
#         res.update(ot_advance_filing=bool(self.env['ir.config_parameter'].sudo().get_param('overtime.ot_advance_filing')))
#         return res

#     @api.multi
#     def set_values(self):
#         super(ResConfigSettings, self).set_values()
#         self.env['ir.config_parameter'].sudo().set_param('overtime.ot_advance_filing', self.ot_advance_filing)
