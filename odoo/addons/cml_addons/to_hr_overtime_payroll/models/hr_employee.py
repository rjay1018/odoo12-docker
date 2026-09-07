from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    
    overtime_line_ids = fields.One2many('hr.overtime.line', 'employee_id', string='Overtime', domain=[('state','in',('approved','done'))],
                                           store=True, index=True,
                                           help='Approved Overtime Declaration Lines')
    
    unpaid_overtime_line_ids = fields.One2many('hr.overtime.line', 'employee_id', string='Unpaid Overtime',
                                                   domain=[('state','=','approved'), ('payslip_id','=', False)], index=True,
                                                   help='Approved Overtime Declaration Lines those have not been included in any payslip yet')
    
    overtime_approving_user_id = fields.Many2one('res.users', string='Overtime Approver', compute='_compute_default_approver',
                                           help='The user who will be the default user to take approval action for his subordinate')
    

    def _compute_default_approver(self):
        for r in self:
            r.overtime_approving_user_id = r._get_approver()
    
    @api.model
    def _is_approver(self):
        if self.user_id:
            if self.user_id.has_group('to_hr_overtime_payroll.group_hr_overtime_user'):
                return True
        else:
            return False
    
    @api.model
    def _get_approver(self):
        employee_id = self
        department_id = self.department_id
        while (employee_id.parent_id or (department_id and department_id.manager_id)):
            if employee_id.parent_id._is_approver():
                return employee_id.parent_id.user_id
            if department_id.manager_id._is_approver():
                return department_id.manager_id.user_id
            employee_id = employee_id.parent_id
            department_id = department_id.parent_id
        return False
            
            
    