from openerp import models, api, fields


class CrmAppointmentWizard(models.TransientModel):
    _name = "crm.appointment.wizard"

    partner_id = fields.Many2one(
        'res.partner',
        required=True,
        string='Client'
    )
    employee_id = fields.Many2one(
        'hr.employee',
        required=True,
        string='Specialist'
    )

    def action_submit_appointment(self):
        crm_ref_id = self._context.get('active_id')
        crm_lead_id = self.env['crm.lead'].browse(crm_ref_id)
        res = self.env['clinic.appointment'].create({
            'partner_id': self.partner_id.id,
            'employee_id': self.employee_id.id,
            'crm_id': crm_lead_id.id,
            'appointment_type': crm_lead_id.appointment_type,
            'product_id': crm_lead_id.product_id.id,
            'clinic_id': crm_lead_id.clinic_id.id,
            'session_start': crm_lead_id.session_start
        })
        act = self.env.ref('cml_clinic.action_appointment').read([])[0]
        act['domain'] = [('id', '=', res.id)]
        act['views'] = [(self.env.ref('cml_clinic.appointment_tree').id, 'tree'),
                        (self.env.ref('cml_clinic.appointment_form').id, 'form')]
        return act

    @api.model
    def default_get(self, fields_list):
        result = super(CrmAppointmentWizard, self).default_get(fields_list)
        active_id = self._context.get('active_id', False)
        crm_lead_id = self.env['crm.lead'].browse(active_id)
        result.update({
            'partner_id': crm_lead_id.partner_id.id,
            'employee_id':crm_lead_id.employee_id.id

        })
        return result
