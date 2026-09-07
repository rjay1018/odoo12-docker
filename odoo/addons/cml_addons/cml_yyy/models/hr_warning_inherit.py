from odoo import models, fields, api, _

class HrAnnouncementTable(models.Model):
    _inherit = 'hr.announcement'

    user_ids = fields.Many2many('res.users', string="Users")
    announcement_type = fields.Selection(
        [('employee', 'By Employee'), ('department', 'By Department'), ('job_position', 'By Job Position')
            , ('user', 'User')
         ])
