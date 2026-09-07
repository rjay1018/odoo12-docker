from odoo import models, fields

class HrContract(models.Model):
    _inherit = 'hr.contract'    
    
    
    overtime_allowance = fields.Boolean(string='Overtime Allowance', default=False)
    