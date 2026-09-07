from odoo import models, fields, api


class CrmLeadInherit(models.Model):
    _inherit = 'crm.lead'

    appointment_type = fields.Selection(
        string='Appointment Type',
        selection=[('inclinic', 'In-Clinic'), ('online', 'Online')]
    )
    product_id = fields.Many2one(
        string='Service',
        comodel_name='product.product',
        domain=[('type', '=', 'service',)]
    )
    # partner_id = fields.Many2one(
    #     string='Client',
    #     comodel_name='res.partner',
    #     domain=[('customer', '=', 'True',)]
    # )
    clinic_id = fields.Many2one(
        'res.clinic',
        string="Clinic"
    )
    employee_id = fields.Many2one(
        string='Specialist',
        comodel_name='hr.employee',
        required=True
    )
    session_start = fields.Datetime(
        string='Start',
        readonly=True,
        default=fields.Datetime.now,
    )
    def action_open_appointment_count(self):
        act = self.env.ref('cml_clinic.action_appointment').read([])[0]
        act['domain'] = [('crm_id', '=', self.id)]
        act['views'] = [(self.env.ref('cml_clinic.appointment_tree').id, 'tree'), (self.env.ref('cml_clinic.appointment_form').id, 'form')]
        return act
