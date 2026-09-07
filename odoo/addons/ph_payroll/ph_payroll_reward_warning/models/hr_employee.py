from odoo import models, fields, api, _


class HrAnnouncements(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    def _announcement_count(self):
        for obj in self:
            announcement_ids = self.env['hr.announcement'].sudo().search([('is_announcement', '=', True),
                                                                          ('state', 'in', ('approved', 'done'))])
            obj.announcement_count = len(announcement_ids)

    @api.multi
    def announcement_view(self):
        for obj in self:
            ann_obj = self.env['hr.announcement'].sudo().search([('is_announcement', '=', True),
                                                                 ('state', 'in', ('approved', 'done'))])
            ann_ids = []
            for each in ann_obj:
                ann_ids.append(each.id)
            view_id = self.env.ref('ph_payroll_reward_warning.view_hr_announcement_form').id
            if ann_ids:
                if len(ann_ids) > 1:
                    value = {
                        'domain': str([('id', 'in', ann_ids)]),
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        'res_model': 'hr.announcement',
                        'view_id': False,
                        'type': 'ir.actions.act_window',
                        'name': _('Announcements'),
                        'res_id': ann_ids
                    }
                else:
                    value = {
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'hr.announcement',
                        'view_id': view_id,
                        'type': 'ir.actions.act_window',
                        'name': _('Announcements'),
                        'res_id': ann_ids and ann_ids[0]
                    }
                return value

    announcement_count = fields.Integer(compute='_announcement_count', string='# Announcements')