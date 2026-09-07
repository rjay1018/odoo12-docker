# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError


class Appointments(models.Model):
    _inherit = 'clinic.appointment'

# New Added Fields 02/20/2023
    with_prescription = fields.Boolean(
        string='With Prescription?',
        store=True
    )
    
    with_medcert = fields.Boolean(
        string='With MedCert?',
        store=True
    )

    was_rescheduled = fields.Boolean(
        string='Rescheduled Appointment',
        store=True
    )
# New Added Fields 02/20/2023

    invoice_count = fields.Integer(
        string='Invoice Count',
        compute='_get_invoiced',
        readonly=True,
        store=True,
    )
    invoice_status = fields.Selection(
        [
            ('paid', 'Paid'),
            ('unpaid', 'Un-Paid')
        ],
        default="unpaid",
        compute="_get_invoiced",
    )
    # state = fields.Selection(
    #     selection_add=[
    #         ('book', 'Booked')]
    # )
    state = fields.Selection(
        string='Status',
        selection=[('draft', 'Draft'),
                   ('book', 'Booked'),
                   ('confirmed', 'Confirmed'),
                   ('done', 'Done'),
                   ('validated', 'Validated'),
                   ('rescheduled', 'Rescheduled'),
                   ('cancel', 'Cancelled')],
        default='draft',
        track_visibility="always",
        readonly=True,
    )
    feedback_radio_option = fields.Selection(
        [
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
            ('6', '6'),
            ('7', '7'),
            ('8', '8'),
            ('9', '9'),
            ('10', '10')
        ],
        string="Ratings"
    )
    feedback_message = fields.Text(
        string="Message"
    )
    show_create_invoice = fields.Boolean(
        default=True
    )
    multi_service_ids = fields.One2many(
        'cml.multi.service.line',
        'appoint_id',
    )
    partner_employee_id = fields.Many2one(
        string='Partner Specialist',
        comodel_name='hr.employee',
        readonly=True,
        compute="_compute_history",
        store=True
    )
    specialist_email = fields.Char(
        string='Specialist Email',
        related='partner_employee_id.work_email',
        readonly=True,
        store=True
    )
    specialist_jobtitle = fields.Char(
        string='Job Title',
        related='partner_employee_id.job_title',
        readonly=True,
        store=True
    )
    appointment_ids = fields.Many2many(
        'clinic.appointment',
        'clinic_appointment_relational',
        'appointment_id',
        'specialist_email',
        string='Appointment',
        domain=[('session_start', '>', fields.Date.today())]
    )
    appt_history_ids = fields.Many2many(
        'clinic.appointment',
        'clinic_appointment_relational_new',
        'appointment_id',
        'specialist_jobtitle',
        string='Appointment',
        compute="_compute_history",
        domain=[('session_start', '<', fields.Date.today())]
    )
    referral_ids = fields.Many2many(
        'client.referral',
        string='Referral Records',
        compute="_compute_history",
    )
    helpline_ids = fields.Many2many(
        'helpline.sessions',
        string="Helpline Record",
        compute="_compute_history",
    )
    file_ids = fields.Many2many(
        'muk_dms.file',
        string='Client Files',
        compute="_compute_history",
    )
    survey_input_count = fields.Integer(
        string='Survey number', compute='_compute_survey_input_count',
        store=True
    )

    clinic_id = fields.Many2one(
        'res.clinic',
        string="Clinic"
    )
    start_date = fields.Datetime(
        string='Session Start',
        readonly=True,
        # states={'confirmed': [('readonly', False)]},
    )

    stop_date = fields.Datetime(
        string='Session Stop',
        readonly=True,
        # states={'confirmed': [('readonly', False)]},
    )
    invoice_ids = fields.One2many(
        'account.invoice',
        'appointment_id'
    )
    invoice_type = fields.Selection(
        [
            ('not_invoice', 'Not Invoice'),
            ('paid', 'Paid'),
            ('invoice', 'Invoice'),
        ],
        store=True,
        string="Invoice Type",
        compute='_compute_invoice_type'
    )

    @api.depends('invoice_ids.state', 'state')
    def _compute_invoice_type(self):
        for rec in self:
            if rec.invoice_ids.filtered(lambda inv: inv.state == 'paid'):
                rec.invoice_type = 'paid'
            elif rec.invoice_ids:
                rec.invoice_type = 'invoice'
            else:
                rec.invoice_type = 'not_invoice'

    @api.depends('partner_id.survey_inputs')
    def _compute_survey_input_count(self):
        for survey in self:
            survey.survey_input_count = len(survey.partner_id.survey_inputs)

    @api.depends("partner_id")
    def _compute_history(self):
        for rec in self:
            rec.partner_employee_id = rec.partner_id.employee_id.id
            rec.appt_history_ids = [(6, 0, rec.partner_id.appt_history_ids.ids)]
            rec.referral_ids = [(6, 0, rec.partner_id.referral_ids.ids)]
            rec.helpline_ids = [(6, 0, rec.partner_id.helpline_ids.ids)]
            rec.file_ids = [(6, 0, rec.partner_id.file_ids.ids)]

    def action_survey_input(self):
        act = self.env.ref('partner_survey.act_partner_survey_input').read([])[0]
        act['context'] = {'search_default_partner_id': self.partner_id.id, 'default_partner_id': self.partner_id.id}
        return act

    def action_start(self):
        for rec in self:
            rec.start_date = fields.Datetime.now()

    def action_stop(self):
        for rec in self:
            rec.stop_date = fields.Datetime.now()

    def action_book(self):
        self.write({
            'state': 'book'
        })
        
    def action_rescheduled(self):
        self.write({
            'state': 'cancel',
            'was_rescheduled': True
        })


#    @api.constrains('session_end', 'session_start', 'clinic_id')
#    def _duration_validation(self):
#        res = self.env['clinic.appointment'].search(
#            [('clinic_id', '=', self.clinic_id.id), ('session_start', '>=', self.session_start),
#             ('session_end', '<=', self.session_end), ('id', '!=', self.id)])
#        if res:
#            raise ValidationError(_("Appointment is already booked"))

    @api.model
    def create(self, vals):
        call_super = super(Appointments, self).create(vals)
        call_super.set_multi_lines()
        return call_super

    def action_view_invoice(self):
        act = self.env.ref("account.action_invoice_tree1")
        act_read = act.read([])[0]
        act_read['domain'] = [('appointment_id', '=', self.id)]
        return act_read

    def _get_invoiced(self):
        for rec in self:
            invoice_ids = self.env['account.invoice'].sudo().search([('appointment_id', '=', rec.id)])
            invoice_status = invoice_ids.filtered(lambda l: l.state not in ['paid'])
            if invoice_status or not invoice_ids:
                rec.invoice_status = "unpaid"
            else:
                rec.invoice_status = "paid"
            rec.invoice_count = len(invoice_ids)

    def action_create_invoice(self):
        invoice_lines = self.multi_service_ids
        if invoice_lines:
            invoice_id = self.env['account.invoice'].sudo()
            invoice_line_id = self.env['account.invoice.line'].sudo()
            if not self.partner_id:
                raise exceptions.UserError("Please select valid Client!")
            invoice = invoice_id.create({
                'partner_id': self.partner_id.id,
                'account_id': self.partner_id.property_account_receivable_id.id,
                'fiscal_position_id': self.partner_id.property_account_position_id.id,
                'appointment_id': self.id,
                'name': self.sequence,
                'date_invoice': fields.Date.today(),
                'origin': self.sequence,
                'origin_id': self.id,
            })
            for line in invoice_lines:
                line_values = {
                    'product_id': line.service_id.id,
                    'name': line.service_id.name or "",
                    'invoice_id': invoice.id
                }
                invoice_line = invoice_line_id.new(line_values)
                invoice_line['quantity'] = line.qty_to_invoice
                invoice_line._onchange_product_id()
                invoice_line._onchange_account_id()
                invoice_line._onchange_uom_id()
                line_values = invoice_line._convert_to_write({name: invoice_line[name] for name in invoice_line._cache})
                line_values['price_unit'] = line.unit_price
                invoice.write({'invoice_line_ids': [(0, 0, line_values)]})
                invoice.compute_taxes()
            return invoice

    @api.onchange('product_id')
    def set_multi_lines(self):
        for rec in self:
            if rec.product_id:
                id = rec.multi_service_ids.filtered(lambda l: l.is_from_appoint == True)
                if id:
                    id[0].service_id = rec.product_id.id
                    id[0]._onchange_service_id()
                else:
                    rec.multi_service_ids = [(0, 0, {
                        'service_id': rec.product_id.id,
                        'qty': '1',
                        'unit_price': rec.product_id.lst_price,
                        'is_from_appoint': True
                    })]

    # def action_apply_free_session(self):
    #     pass


class Multi_invoice_services(models.Model):
    _name = 'cml.multi.service.line'

    appoint_id = fields.Many2one(
        'clinic.appointment'
    )
    service_id = fields.Many2one(
        'product.product',
        string="Service",
        required=True
    )
    qty = fields.Float(
        "Qty",
        default=1
    )
    qty_to_invoice = fields.Float(
        "Qty to Invoice"
    )
    invoiced_qty = fields.Float(
        "Invoiced Qty"
    )
    unit_price = fields.Float(
        "Price"
    )
    total_price = fields.Float(
        "Total",
        compute="_set_total_price"
    )
    is_from_appoint = fields.Boolean(
        default=False
    )

    @api.constrains('qty_to_invoice')
    def _validate_qty_invoice(self):
        for rec in self:
            if rec.qty_to_invoice > (rec.qty - rec.invoiced_qty):
                raise exceptions.UserError("You have only %s Qty Available." % ((rec.qty - rec.invoiced_qty)))

    @api.onchange('qty', 'invoiced_qty')
    def _set_invoice_qty(self):
        for rec in self:
            rec.qty_to_invoice = rec.qty - rec.invoiced_qty

    @api.onchange('qty', 'unit_price')
    def _set_total_price(self):
        for rec in self:
            rec.total_price = rec.qty * rec.unit_price

    @api.onchange('service_id')
    def _onchange_service_id(self):
        for rec in self:
            if rec.service_id:
                rec.unit_price = rec.service_id.lst_price
            else:
                rec.unit_price = 0
