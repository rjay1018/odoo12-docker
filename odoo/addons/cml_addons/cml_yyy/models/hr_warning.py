from odoo import fields, models

class HrAnnouncementTable(models.Model):
    _inherit = 'hr.announcement'

    announcement_type = fields.Selection([
        ('employee', 'By Employee'),
        ('department', 'By Department'),
        ('job_position', 'By Job Position'),
        ('user', 'User')
    ])
    user_ids = fields.Many2many('res.users', 'announcement_user_rel', 'announcement_id', 'user_id', string="Users")
