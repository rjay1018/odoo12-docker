from odoo import models, fields, api, _


class HrOvertimeReason(models.Model):
    _name = 'hr.overtime.reason'
    _description = 'Overtime Reason'

    name = fields.Char(string='Title', required=True, translate=True)
    description = fields.Text(string='Description')
    allow_working_schedule_overlap = fields.Boolean(string='Allow Overlap Working Schedule', default=False,
                                                    help="If checked, an overtime declaration that overlaps the employee's working "
                                                    "schedule will be allowed. This is helpful for some use cases (working on"
                                                    " compensatory leave days, etc)")

    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         "The reason title must be unique"),
    ]

    @api.multi
    def name_get(self):
        result = []
        for r in self:

            if r.allow_working_schedule_overlap:
                result.append((r.id, '%s - %s' % (r.name, _("Allow Overlap Working Schedule"))))
            else:
                result.append((r.id, '%s - %s' % (r.name, _("Not Allow Overlap Working Schedule"))))
        return result

#     @api.model
#     def name_search(self, name, args=None, operator='ilike', limit=100):
#         args = args or []
#         domain = []
#         if name:
#             domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
#         tags = self.search(domain + args, limit=limit)
#         return tags.name_get()
