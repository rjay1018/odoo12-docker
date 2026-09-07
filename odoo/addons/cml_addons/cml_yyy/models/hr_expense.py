from odoo import fields, models, api


class HrExpenseYYY(models.Model):  
    _inherit = 'hr.expense'

    
    department_id = fields.Many2one(
        string='Department',
        related='employee_id.department_id',
        readonly=True,
        store=True
    )