from odoo import models, fields, api


class OrientationKSO(models.Model):
    _inherit = 'employee.orientation'

    department = fields.Many2one('hr.department', string='SATO/UNIT/CLUSTER/SECTOR', related='employee_name.department_id', required=True)
