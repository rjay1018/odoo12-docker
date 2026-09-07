from odoo import api, fields, models, _


class ReportPrintInvoice(models.TransientModel):
    _name = 'report.print.invoice'

    report_id = fields.Many2one('ir.actions.report', required=True, domain=[])
    wizard_report_ids = fields.Many2many('ir.actions.report', string="Report", copy=False)

    def action_print_report(self):
        result = self.env[self._context['active_model']].browse(self._context['active_id'])
        result.report_ids = [(4, self.report_id.id)]
        action_report = self.report_id.report_action(result)
        action_report.update({'close_on_report_download': True})
        return action_report

    @api.model
    def default_get(self, fields):
        res = super(ReportPrintInvoice, self).default_get(fields)
        active_id = self._context.get('active_id')
        id_brows = self.env['account.payment'].browse(active_id)
        res['wizard_report_ids'] = id_brows.report_ids.ids
        return res
