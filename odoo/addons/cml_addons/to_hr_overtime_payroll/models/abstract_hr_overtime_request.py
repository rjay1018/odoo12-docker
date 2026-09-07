from odoo import models, fields, api, _
from odoo.exceptions import UserError
from ..constants import STATES


class AbstractHrOvertimeRequest(models.AbstractModel):
    _name = 'abstract.hr.overtime.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(string='Request Number',
                       required=True,
                       copy=False, readonly=True,
                       index=True, default=lambda self: _('/'))

    user_id = fields.Many2one('res.users', string='Submitted By',
                              required=True,
                              default=lambda self: self.env.user)

    state = fields.Selection(STATES, string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)

    approved_by = fields.Many2one('res.users', string='Approved By',
                                  help='The user who took approval action on this record', readonly=True,
                                  track_visibility='onchange')

    def _generate_name(self):
        return UserError(_("The method _generate_name() has not been implementation. This could be a programming error."))

    @api.multi
    def unlink(self):
        for r in self:
            if r.state != 'draft':
                raise UserError(_('You cannot delete a request which is not in draft state!'))
        return super(AbstractHrOvertimeRequest, self).unlink()

    @api.multi
    def action_confirm(self):
        for r in self:
            name = r._generate_name()
            r.write({
                'state': 'confirmed',
                'name': name
                })
            r.add_follower()

    @api.multi
    def action_reconfirm(self):
        for r in self:
            if r.state != 'refused':
                raise UserError(_("You cannot confirm while the request %s while its status is not Refused."))
        self.write({'state': 'confirmed'})
        self.add_follower()

    @api.multi
    def action_cancel(self):
        for r in self:
            if r.state not in ('confirmed', 'approved', 'refused'):
                raise UserError(_("You cannot cancel the overtime request %s while its state is neither Confirmed nor Approved nor Refused.")
                                  % (r.name,))
        self.write({'state': 'canceled'})

    @api.multi
    def action_done(self):
        for r in self:
            if r.state != 'approved':
                raise UserError(_("You cannot mark the overtime request %s as Done while it is not in Approved state") % (r.name,))
        self.write({'state': 'done'})

    @api.multi
    def action_approve(self):
        for r in self:
            if r.state != 'confirmed':
                raise UserError(_("The request %s must be in the status of 'Confirmed' before it can be approved!") % (r.name,))
        self.write({
            'state': 'approved',
            'approved_by': self.env.user.id
            })

    @api.multi
    def action_refuse(self):
        user = self.env.user
        for r in self:
            if not r.request_line_ids:
                raise UserError(_('You must create request first.'))

        for r in self.mapped('request_line_ids'):
            if r.state not in ('confirmed', 'approved'):
                raise UserError(_('You can only refuse the requests whose state is either \'Confirmed\' or \'Approved\'.'))

            if r.state == 'approved':
                if not user.has_group('to_hr_overtime_payroll.group_hr_overtime_manager') and not user.id != r.approved_by.id:
                    raise UserError(_('Only Overtime Managers or the one who approved this request can refuse it after its approval'))

            r.action_refuse()

        self.write({'state': 'refused'})

    @api.multi
    def action_draft(self):
        for r in self:
            if not r.request_line_ids:
                raise UserError(_('No request found.'))

        for r in self.mapped('request_line_ids'):
            if r.state not in ('confirmed', 'refused', 'canceled'):
                raise UserError(_('You can only Set to Draft the requests whose state is either \'confirmed\' or \'refused\' or \'Canceled\'.'))

            r.action_draft()

        self.write({'state': 'draft'})

    @api.multi
    def add_follower(self):
        for r in self:
            if r.approving_user_id:
                r.message_subscribe([r.approving_user_id.partner_id.id])
                email_template = self.env.ref('to_hr_overtime_payroll.email_template_overtime_request_confirm')
                if email_template:
                    r.message_post_with_template(email_template.id)

