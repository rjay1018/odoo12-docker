# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError, UserError
from odoo.addons.mail.models import mail_template


class WorkDayType(models.Model):
    _name = 'work.day.type'
    _description = "Work Day Type"
    _order = 'date_from DESC'

    name = fields.Char(string='Title', required=True, help="The name of the type", translate=True)
    rate = fields.Float(string='Allowance Rate', digits=dp.get_precision('Payroll Rate'), default=100.0, help="The rate for allowance in percentage."
                        " For example, you can specify 150 here for 150% so that the salary rule can multiple the basic wage with this rate for, for"
                        " example, overtime.")
    date_from = fields.Date(string='Date From', required=True, help="The starting date of the period. This date is included in the period.")
    date_to = fields.Date(string='Date To (incl.)', required=True, help="The ending date of the period. This date is included in the period.")
    is_holiday = fields.Boolean(string='Holiday Period', default=True, help="This is to indicate if this type is a holiday period")
    company_id = fields.Many2one('res.company', string='Company')

    @api.constrains('date_from', 'date_to', 'company_id')
    def _check_overlap(self):
        WorkDayType = self.env['work.day.type']
        for r in self:
            domain = [
                ('id', '!=', r.id),
                ('date_to', '>', r.date_from),
                ('date_from', '<', r.date_to),
                ]
            if r.company_id:
                domain += [
                    '|',
                        ('company_id', '=', r.company_id.id),
                        ('company_id', '=', False)
                    ]
            overlap = WorkDayType.search(domain, limit=1)
            if overlap:
                raise ValidationError(_("You were trying to create a new Work Day Type that overlapped an existing one, which is %s")
                                      % overlap.display_name)

    @api.multi
    def name_get(self):
        result = []
        normal_work_day = self.env.ref('to_hr_work_day_type.normal_work_day')
        for r in self:
            if r.id != normal_work_day.id:
                name = '%s [%s - %s]' % (r.name, mail_template.format_date(self.env, r.date_from), mail_template.format_date(self.env, r.date_to))
            else:
                name = r.name
            result.append((r.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', ('date_from', '=ilike', '%' + name + '%'), ('date_to', '=ilike', '%' + name + '%'), ('name', operator, name)]
        records = self.search(domain + args, limit=limit)
        return records.name_get()

    @api.multi
    def unlink(self):
        cannot_delete_word_day_type = self.env.ref('to_hr_work_day_type.normal_work_day')
        for r in self:
            if r.id == cannot_delete_word_day_type.id:
                raise UserError(_("You cannot delete the work day type '%s' which is required for some operations.")
                                % cannot_delete_word_day_type.display_name)
        return super(WorkDayType, self).unlink()
