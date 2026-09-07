from openerp import models, api, fields


class RefusalWizard(models.TransientModel):
    _name = "refusal.wizard"

    refusal_reason_id = fields.Many2one(
        string='Reason',
        comodel_name='refusal.reasons',
    )


    def action_confirm(self):
        applicant = self.env['hr.applicant'].browse(self._context.get('active_id'))
        vals = {
             'refusal_reason_id': self.refusal_reason_id.id,
             'active' : False
        }
        return applicant.write(vals)