from odoo import fields, models, api


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    employee_ids = fields.Many2many('hr.employee', 'emp_work_rel', 'work_id', 'emp_id', string="Assigned Workers")
