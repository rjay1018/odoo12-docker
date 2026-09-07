from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    EMP_NAME = [
        (1, 'JOSE PROTASIO RIZAL JR.'),
        (2, 'JOSE P. RIZAL JR.'),
        (3, 'RIZAL JR., JOSE PROTASIO'),
        (4, 'RIZAL JR., JOSE P.')
    ]

    LETTER_CASE = [
        (1, 'UPPER CASE'),
        (2, 'Title Case'),
    ]

    @api.model
    def _get_work_schedule(self):
        return self.env.ref('resource.resource_calendar_std', None).id

    resource_calendar_id = fields.Many2one('resource.calendar', 'Company Working Hours', default=_get_work_schedule)
    employee_name_format = fields.Selection(EMP_NAME, 'Name Format')
    employee_name_letter_case = fields.Selection(LETTER_CASE, 'Letter Case')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            employee_name_format=int(self.env['ir.config_parameter'].sudo().get_param(
                'employee.employee_name_format')),
            employee_name_letter_case=int(self.env['ir.config_parameter'].sudo().get_param(
                'employee.employee_name_letter_case'))
            )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'employee.employee_name_format', self.employee_name_format)
        self.env['ir.config_parameter'].sudo().set_param(
            'employee.employee_name_letter_case', self.employee_name_letter_case)
