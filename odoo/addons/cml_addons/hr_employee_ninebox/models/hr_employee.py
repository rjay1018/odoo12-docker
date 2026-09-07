from odoo import models, fields, api, exceptions, _, SUPERUSER_ID

class HrEmployee(models.Model):
    _inherit = "hr.employee"
    _description = "Employee"

    potential = fields.Selection([('0', "0"),('1', "1"), ('2', "2"),('3', "3")],default='0',string='Potential')
    performance = fields.Selection([('0', "0"),('1', "1"), ('2', "2"),('3', "3")],default='0',string='Performance')
    nbox_rating = fields.Char(string='Nine Box Rating',readonly=True,compute='_compute_nbox_rating')


    @api.depends('potential','performance')
    def _compute_nbox_rating(self):
        if self.potential and self.performance:        
            self.nbox_rating = str(self.potential) + "X" + str(self.performance)        
