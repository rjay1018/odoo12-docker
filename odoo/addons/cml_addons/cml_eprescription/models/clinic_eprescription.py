from odoo import models, fields, api
from num2words import num2words



class ClinicEpresciption(models.Model):
    _name = 'clinic.eprescription'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = 'Clinic E-Presciption'

    _rec_name = 'name'
    _order = 'name ASC'

    @api.model
    def create(self, vals):
        if vals.get('name', ('New')) == ('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('clinic.eprescription.sequence') or ('New')
        result = super(ClinicEpresciption, self).create(vals)
        return result
    
    @api.multi
    def action_send_prescription(self):
        """ Action to send Prescription through Email."""
    #     self.ensure_one()
    #     template = self.env.ref('cml_eprescription.send_eprescription_email')
    #     if template:
    #         self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
    #         self.flag = True
    
    # @api.multi
    # def action_send_email(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('cml_eprescription', 'send_eprescription_email')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'clinic.eprescription',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'sent': True,
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    sent = fields.Boolean(
        string='sent',
    )
    
    name = fields.Char(
        string='Name',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: ('New')
    )
    consulation_date = fields.Date(
        string='Consulation Date',
        default=fields.Date.context_today,
    )
    
    partner_id = fields.Many2one(
        string='Client',
        comodel_name='res.partner',
        ondelete='restrict',
        required=True,
    )
    phone = fields.Char(
        string='Contact No.',
        related='partner_id.mobile'
    )
    
    client_email = fields.Char(
        string='Client Email',
        related='partner_id.email'
    )
    
    client_photo = fields.Binary(
        string='Client Picture',
        related='partner_id.image'
    )
    

    employee_id = fields.Many2one(
        string='Specialist',
        comodel_name='hr.employee',
        ondelete='restrict',
        required=True,
    )
    
    emp_phone = fields.Char(
        string='Specialist Contact No.',
        related='employee_id.mobile_phone'
    )

    prc_number = fields.Char(
        string='PRC Number',
    )
    
    ptr_number = fields.Char(
        string='PTR Number',
    )

    
    s2_license = fields.Char(
        string='S2 License',
    )
    
    valid_until = fields.Date(
        string='Valid Until',
        default=fields.Date.context_today,
    )
    
    prescription = fields.Html(
        string='Prescription',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False
    )

    prescription_line_ids = fields.One2many(
        string='Prescription Line',
        comodel_name='prescription.line',
        inverse_name='prescription_id',
    )
    
    source = fields.Char(
        string='Appointment Number',
        readonly=True 
    )

    user_id = fields.Many2one('res.users','Current User', default=lambda self: self.env.user)

    doc_signature = fields.Binary(
        string='Signature',
        related='user_id.digital_signature'
    )

class PrescriptionLine(models.Model):
    _name = 'prescription.line'
    _description = 'Prescription Line'

    _rec_name = 'name'
    _order = 'name ASC'

    @api.multi
    def _compute_amount_in_word(self):
        for rec in self:
            rec.num_word = num2words(rec.qty)

    name = fields.Char(
        string='Medicine/Drug Name',
        required=True,
    )
    prescription = fields.Text(
        string='Prescription',
    )
    qty = fields.Float(
        string='Quantity',
    )
    prescription_id = fields.Many2one(
        string='Prescription',
        comodel_name='clinic.prescription',
    )
    no_refill = fields.Boolean(
        string='No Refill',
    )
    num_word = fields.Char(
        string="Qty in words",
        compute='_compute_amount_in_word'
    )
    uom = fields.Char(
        string='Units',
    )
    