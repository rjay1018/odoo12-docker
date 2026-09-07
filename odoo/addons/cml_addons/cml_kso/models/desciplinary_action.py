from odoo import models, fields, api

class Discplinary_additional(models.Model):
    _inherit = 'disciplinary.action'
    
    date_violation = fields.Date(string="Date of Violation")
    date_issued=fields.Date(string="Date Issued")
    name=fields.Char(string='Reference', required=True, copy=False, readonly=True,
                       default=lambda self: ('Pink Slip'))
    department_name = fields.Many2one('hr.department', string='SATO/UNIT/CLUSTER/SECTOR', required=True)
    discipline_reason = fields.Many2one('discipline.category', string='Violation', required=True)
    
    position = fields.Char(related='employee_name.job_id.name', string='Position')