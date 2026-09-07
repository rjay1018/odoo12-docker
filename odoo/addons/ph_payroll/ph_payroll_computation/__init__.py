from . import models
from . import reports

# from odoo import api, SUPERUSER_ID, _, tools

# def _configure_journals(cr, registry):
#     env = api.Environment(cr, SUPERUSER_ID, {})

#     company_ids = env['res.company'].search([('chart_template_id', '!=', False)])
#     for company in company_ids:

#         # Create Salary Journal
#         salary_journal = env['account.journal'].search([
#             ('name', '=', _('Salary')),
#             ('company_id', '=', company.id),
#             ('type', '=', 'general')], limit=1)
#         if not salary_journal:
#             env['account.journal'].create({
#                 'name': _('Salary'),
#                 'type': 'general',
#                 'code': 'SAL',
#                 'company_id': company.id,
#                 'show_on_dashboard': True
#                 })