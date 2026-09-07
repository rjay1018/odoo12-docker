from datetime import date, datetime, timedelta
from dateutil import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class EmergencyContact(models.Model):
    _name = 'hr.emergency.contact'
    _description = 'HR Emergency Contact'

    name = fields.Char(required=True)
    contact_no = fields.Char()
    relation = fields.Char(string='Relation with Employee')
    employee_id = fields.Many2one('hr.employee')


# class EmployeeFamily(models.Model):
#     _name = 'hr.employee.family'
#     _description = 'HR Employee Family'

#     RELATION = [
#         ('father', 'Father'),
#         ('mother', 'Mother'),
#         ('daughter', 'Daughter'),
#         ('son', 'Son'),
#         ('wife', 'Wife')
#     ]


#     employee_id = fields.Many2one('hr.employee', string="Employee", invisible=1)
#     member_name = fields.Char(string='Name')
#     relation = fields.Selection(RELATION, string='Relationship', help='Relation with employee')
#     member_contact = fields.Char(string='Contact No')


class Employee(models.Model):
    _inherit = 'hr.employee'

    EMP_STATUS = [
        ('regular', 'Regular/Permanent'),
        ('probation', 'Probationary'),
        ('temporary', 'Temporary'),
        ('contract', 'Fixed Term/Contractual'),
    ]

    LEAVE_STATUS = [
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('for_approval', 'Recommending Approval'),
        ('approve', 'Approved'),
        ('cancel', 'Cancelled')
    ]

    def mail_reminder(self):
        now = datetime.now() + timedelta(days=1)
        date_now = now.date()
        match = self.search([])
        for i in match:
            if i.id_expiry_date:
                exp_date = fields.Date.from_string(i.id_expiry_date) - timedelta(days=14)
                if date_now >= exp_date:
                    mail_content = "  Hello  " + i.name + ",<br>Your ID " + i.identification_id + "is going to expire on " + \
                                   str(i.id_expiry_date) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('ID-%s Expired On %s') % (i.identification_id, i.id_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()
        match1 = self.search([])
        for i in match1:
            if i.passport_expiry_date:
                exp_date1 = fields.Date.from_string(i.passport_expiry_date) - timedelta(days=180)
                if date_now >= exp_date1:
                    mail_content = "  Hello  " + i.name + ",<br>Your Passport " + i.passport_id + "is going to expire on " + \
                                   str(i.passport_expiry_date) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('Passport-%s Expired On %s') % (i.passport_id, i.passport_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()

    def format_name(self):
        name = ''
        name_format = int(self.env['ir.config_parameter'].sudo().get_param('employee.employee_name_format'))
        if not name_format:
            name_format = 4 # Set the default to 'RIZAL JR., JOSE P.'

        fn = self.first_name
        mn = self.middle_name
        mi = self.middle_name[0] + '.' if self.middle_name else ''
        ln = self.last_name
        en = ' %s' % (self.extension_name) if self.extension_name else ''

        if name_format == 1:
            name = "%s %s %s%s" % (fn, mn, ln, en)
        elif name_format == 2:
            name = "%s %s %s%s" % (fn, mi, ln, en)
        elif name_format == 3:
            name = "%s%s, %s %s" % (ln, en, fn, mn)
        else:
            name = "%s%s, %s %s" % (ln, en, fn, mi)
        return (name).strip()

    @api.onchange('last_name', 'first_name', 'middle_name', 'extension_name')
    def onchange_name(self):
        letter_case = int(self.env['ir.config_parameter'].sudo().get_param('employee.employee_name_letter_case'))
        if not letter_case:
            letter_case = 1 # Set the default to upper()

        fn = (self.first_name).strip() if self.first_name else ''
        mn = (self.middle_name).strip() if self.middle_name else ''
        ln = (self.last_name).strip() if self.last_name else ''
        en = (self.extension_name).strip() if self.extension_name else ''

        if letter_case == 1:
            self.last_name = (ln).upper()
            self.first_name = (fn).upper()
            self.middle_name = (mn).upper()
            self.extension_name = (en).upper()
        else:
            self.last_name = (ln).title()
            self.first_name = (fn).title()
            self.middle_name = (mn).title()
            self.extension_name = en # regular format applied just in case value of ext. name is (II, III, IV, etc.)
        self.name = self.format_name()

    @api.model
    def _get_work_schedule(self):
        return self.env.ref('resource.resource_calendar_std', None).id

    @api.multi
    @api.depends('joining_date', 'retire_date')
    def _compute_years_in_service(self):
        for obj in self:
            today = datetime.today().date()
            join_date = fields.Date.to_date(obj.joining_date)
            retire_date = fields.Date.to_date(obj.retire_date)

            if not obj.retire_date:
                d = relativedelta.relativedelta(today, join_date)
            else:
                d = relativedelta.relativedelta(retire_date, join_date)

            obj.yis_months = d.years + (d.months / 12)

            yr_mo = ''
            yr = mo = ''

            if d.years == 1:
                yr = ' year'
            elif d.years > 1:
                yr = ' years'

            if d.months == 1:
                mo = ' month'
            elif d.months > 1:
                mo = ' months'

            if yr or mo:
                if d.years == 0 and d.months > 0:
                    yr_mo = str(d.months) + mo
                elif d.years > 0 and d.months == 0:
                    yr_mo = str(d.years) + yr
                elif d.years > 0 and d.months > 0:
                    yr_mo = str(d.years) + yr + ' & ' + str(d.months) + mo

            obj.years_in_service = yr_mo

    @api.multi
    def _cron_years_in_service(self):
        employees = self.search([('joining_date', '!=', False)])
        for emp in employees:
            emp._compute_years_in_service()

    @api.multi
    @api.depends('birthday')
    def _compute_age(self):
        for obj in self:
            if obj.birthday:
                delta = date.today() - obj.birthday
                obj.age = (delta.days // 365)

    @api.multi
    def _cron_compute_age(self):
        employees = self.search([('birthday', '!=', False)])
        for emp in employees:
            emp._compute_age()

    department_id = fields.Many2one('hr.department', 'Department', ondelete='restrict')
    resource_calendar_id = fields.Many2one('resource.calendar', 'Work Schedule', default=_get_work_schedule)
    identification_id = fields.Char(string='Employee No.')
    personal_mobile = fields.Char(string='Mobile No.', related='address_home_id.mobile', store=True)
    personal_email = fields.Char(string='Email', related='address_home_id.email', store=True)
    joining_date = fields.Date(string='Hired Date')
    retire_date = fields.Date(string='Retirement Date')
    yis_months = fields.Float(compute='_compute_years_in_service', store=True)
    years_in_service = fields.Char(compute='_compute_years_in_service', string='Years in Service', store=True)
    id_expiry_date = fields.Date(string='Emp. ID Expiry Date', help='Expiry date of Employee ID')
    passport_expiry_date = fields.Date(string='Expiry Date', help='Expiry date of Passport ID')
    id_attachment_id = fields.Many2many('ir.attachment', 'id_attachment_rel', 'id_ref', 'attach_ref', string="Attachment", help='You can attach the copy of your Id')
    passport_attachment_id = fields.Many2many('ir.attachment', 'passport_attachment_rel', 'passport_ref', 'attach_ref1', string="Attachment", help='You can attach the copy of Passport')
    # fam_ids = fields.One2many('hr.employee.family', 'employee_id', string='Family', help='Family Information')
    emergency_contacts = fields.One2many('hr.emergency.contact', 'employee_id', string='Emergency Contact')

    employment_status = fields.Selection(EMP_STATUS, default='regular')

    pagibig_id = fields.Char(string='Pag-Ibig')
    phic_id = fields.Char(string='PhilHealth')
    sss_id = fields.Char(string='SSS')
    tin = fields.Char(string='TIN')
    max_loan = fields.Float(string='Max. Loan Amount', help='Keep zero for open loanable amount')

    training_ids = fields.Many2many(comodel_name='hr.training')
    partner_id = fields.Many2one('res.partner', string='Related Partner')
    payroll_master = fields.Boolean(string='Payroll Master')
    current_leave_state = fields.Selection(compute='_compute_leave_status', string="Current Leave Status", selection=LEAVE_STATUS)

    last_name = fields.Char(required=False)
    first_name = fields.Char(required=False)
    middle_name = fields.Char(required=False)
    extension_name = fields.Char()

    salary_atm = fields.Boolean('Salary Through ATM', default=True)
    certificate = fields.Selection(selection_add=[('doctor', 'Doctor')], string='Certificate Level', default='master', groups="hr.group_hr_user")

    age = fields.Integer(compute='_compute_age', store=True)

    def _get_company_address(self):
        addr_list = []
        partner = self.company_id.partner_id
        
        addr_list.append((partner.street).strip() if partner.street else '')
        addr_list.append((partner.street2).strip() if partner.street2 else '')
        addr_list.append((partner.city).strip() if partner.city else '')
        addr_list.append((partner.state_id.name).strip() if partner.state_id else None)
        addr_list.append((partner.zip).strip() if partner.zip else '')
        addr_list.append((partner.country_id.name).strip() if partner.country_id else None)

        addr = filter(None, addr_list)
        return ', '.join(addr)

    def _sync_user(self, user):
        vals = {}
        if user.tz:
            vals['tz'] = user.tz
        return vals

    def create_partner(self):
        obj_partner = self.env['res.partner']
        if self.partner_id:
            raise ValidationError(_('This employee already has related partner'))

        vals = {
            'name': self.format_name(),
            # 'last_name': self.last_name,
            # 'first_name': self.first_name,
            # 'middle_name': self.middle_name,
            # 'extension_name': self.extension_name,
            'company_type': 'person',
            'customer': True,
            'supplier': True
        }
        new_partner = obj_partner.create(vals)
        self.partner_id = new_partner.id
        self.address_home_id = new_partner.id

    def create_user(self):
        obj_user = self.env['res.users']
        fn = self.first_name
        ln = self.last_name

        partner_id = None
        if self.partner_id:
            partner_id = self.partner_id.id
        
        login = ((fn)[:2]).lower() + (''.join((ln.split(' '))).strip()).lower()

        vals = {
            'name': self.name,
            'login': login,
            'partner_id': partner_id
        }
        new_user = obj_user.create(vals)
        self.user_id = new_user.id
        if not self.partner_id:
            self.partner_id = new_user.partner_id.id
            self.address_home_id = new_user.partner_id.id

            p = self.partner_id
            # p.last_name = ln
            # p.first_name = fn
            # p.middle_name = self.middle_name
            # p.extension_name = self.extension_name
            p.company_type = 'person'
            p.customer = True
            p.supplier = True

        groups_id = []
        groups_id.append(self.env.ref('base.group_user').id)
        groups_id.append(self.env.ref('ph_payroll_leave.grp_emp_own_leave').id)
        groups_id.append(self.env.ref('ph_payroll_overtime.grp_emp_own_ot').id)
        new_user.groups_id = [(6,0, groups_id)]


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    partner_id = fields.Many2one('res.partner', 'Account Holder', ondelete='cascade', index=True,
        domain=['|', ('is_company', '=', True), ('parent_id', '=', False)], required=False)


class Training(models.Model):
    _name = 'hr.training'

    name = fields.Char(required=True)
    date = fields.Date(required=True, default=lambda *d: date.today())
    duration = fields.Float(string='# of Days')
    notes = fields.Text(string='Description')
    location = fields.Char()
    resource_speaker = fields.Char()
    rate = fields.Float()
    employee_ids = fields.Many2many(comodel_name='hr.employee')


class Partner(models.Model):
    _inherit = 'res.partner'

    # def format_name(self):
    #     mi = ex = ''
    #     mn = self.middle_name if self.middle_name else ''
    #     ex = ' %s' % self.extension_name if self.extension_name else ''
    #     if mn:
    #         mi = (mn[0]) + '.'
    #     name = "%s%s, %s %s" % (self.last_name, ex, self.first_name, mi)
    #     return (name).strip()

    # @api.onchange('last_name', 'first_name', 'middle_name', 'extension_name')
    # def onchange_name(self):
    #     self.last_name = (self.last_name).upper().strip() if self.last_name else ''
    #     self.first_name = (self.first_name).upper().strip() if self.first_name else ''
    #     self.middle_name = (self.middle_name).upper().strip() if self.middle_name else ''
    #     self.extension_name = (self.extension_name).upper().strip() if self.extension_name else ''
    #     self.name = self.format_name()

    # last_name = fields.Char()
    # first_name = fields.Char()
    # middle_name = fields.Char()
    # extension_name = fields.Char()

    @api.multi
    def _format_company_header(self, partner=None):
        data = {}
        street = []
        city = []
        country = []

        street.append((partner.street).strip() if partner.street else '')
        street.append((partner.street2).strip() if partner.street2 else '')
        addr_street = filter(None, street)
        data['street'] = ', '.join(addr_street)

        city.append((partner.city).strip() if partner.city else '')
        city.append((partner.state_id.name).strip() if partner.state_id else None)
        addr_city = filter(None, city)
        data['city'] = ', '.join(addr_city)
        
        country.append((partner.zip).strip() if partner.zip else '')
        country.append((partner.country_id.name).strip() if partner.country_id else None)
        addr_country = filter(None, country)
        data['country'] = ', '.join(addr_country)

        data['full_address'] = "%s%s%s" %(
            data['street'] + ', ' if data['street'] else '',
            data['city'] + ', ' if data['city'] else '',
            data['country'] if data['country'] else ''
            )
        return data

    def _get_partner_address(self, p):
        addr_list = []
        addr_list.append((p.street).strip() if p.street else '')
        addr_list.append((p.street2).strip() if p.street2 else '')
        addr_list.append((p.city).strip() if p.city else '')
        addr_list.append((p.state_id.name).strip() if p.state_id else None)
        addr_list.append((p.zip).strip() if p.zip else '')
        addr_list.append((p.country_id.name).strip() if p.country_id else None)
        addr = filter(None, addr_list)
        return ', '.join(addr)


class Applicants(models.Model):
    _inherit = 'hr.applicant'

    @api.onchange('last_name', 'first_name', 'middle_name', 'extension_name')
    def onchange_name(self):
        letter_case = int(self.env['ir.config_parameter'].sudo().get_param('employee.employee_name_letter_case'))
        if not letter_case:
            letter_case = 1 # Set the default to upper()

        fn = (self.first_name).strip() if self.first_name else ''
        mn = (self.middle_name).strip() if self.middle_name else ''
        ln = (self.last_name).strip() if self.last_name else ''
        en = (self.extension_name).strip() if self.extension_name else ''

        if letter_case == 1:
            self.last_name = (ln).upper()
            self.first_name = (fn).upper()
            self.middle_name = (mn).upper()
            self.extension_name = (en).upper()
        else:
            self.last_name = (ln).title()
            self.first_name = (fn).title()
            self.middle_name = (mn).title()
            self.extension_name = en # regular format applied just in case value of ext. name is (II, III, IV, etc.)
        self.partner_name = self.format_name()

    def format_name(self):
        name = ''
        name_format = int(self.env['ir.config_parameter'].sudo().get_param('employee.employee_name_format'))
        if not name_format:
            name_format = 4 # Set the default to 'RIZAL JR., JOSE P.'

        fn = self.first_name
        mn = self.middle_name
        mi = self.middle_name[0] + '.' if self.middle_name else ''
        ln = self.last_name
        en = ' %s' % (self.extension_name) if self.extension_name else ''

        if name_format == 1:
            name = "%s %s %s%s" % (fn, mn, ln, en)
        elif name_format == 2:
            name = "%s %s %s%s" % (fn, mi, ln, en)
        elif name_format == 3:
            name = "%s%s, %s %s" % (ln, en, fn, mn)
        else:
            name = "%s%s, %s %s" % (ln, en, fn, mi)
        return (name).strip()

    last_name = fields.Char(required=False)
    first_name = fields.Char(required=False)
    middle_name = fields.Char(required=False)
    extension_name = fields.Char()


    @api.multi
    def create_employee_from_applicant(self):
        """ Create an hr.employee from the hr.applicants """
        employee = False
        for applicant in self:
            contact_name = False
            if applicant.partner_id:
                address_id = applicant.partner_id.address_get(['contact'])['contact']
                contact_name = applicant.partner_id.name_get()[0][1]
            else :
                new_partner_id = self.env['res.partner'].create({
                    'is_company': False,
                    'name': applicant.partner_name,
                    'email': applicant.email_from,
                    'phone': applicant.partner_phone,
                    'mobile': applicant.partner_mobile
                })
                address_id = new_partner_id.address_get(['contact'])['contact']
            if applicant.job_id and (applicant.partner_name or contact_name):
                applicant.job_id.write({'no_of_hired_employee': applicant.job_id.no_of_hired_employee + 1})
                employee = self.env['hr.employee'].create({
                    'name': applicant.partner_name or contact_name,
                    'first_name': applicant.first_name,
                    'middle_name': applicant.middle_name,
                    'last_name': applicant.last_name,
                    'extension_name': applicant.extension_name,
                    'job_id': applicant.job_id.id,
                    'address_home_id': address_id,
                    'department_id': applicant.department_id.id or False,
                    'address_id': applicant.company_id and applicant.company_id.partner_id
                            and applicant.company_id.partner_id.id or False,
                    'work_email': applicant.department_id and applicant.department_id.company_id
                            and applicant.department_id.company_id.email or False,
                    'work_phone': applicant.department_id and applicant.department_id.company_id
                            and applicant.department_id.company_id.phone or False})
                applicant.write({'emp_id': employee.id})
                applicant.job_id.message_post(
                    body=_('New Employee %s Hired') % applicant.partner_name if applicant.partner_name else applicant.name,
                    subtype="hr_recruitment.mt_job_applicant_hired")
            else:
                raise UserError(_('You must define an Applied Job and a Contact Name for this applicant.'))

        employee_action = self.env.ref('hr.open_view_employee_list')
        dict_act_window = employee_action.read([])[0]
        dict_act_window['context'] = {'form_view_initial_mode': 'edit'}
        dict_act_window['res_id'] = employee.id
        return dict_act_window
