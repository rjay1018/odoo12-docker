from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)

class HrContractyyy(models.Model):
    _inherit = 'hr.contract'

    position_allowance = fields.Float(string="Position Allowance")


# class HrLoan(models.Model):
#     _inherit = 'hr.loan'
#     reasons = fields.Text(string='Reasons')

#     paid_total = fields.Float(
#         string='Total Paid Amount',

#         compute='_compute_loan_amount'
#     )
#     balance_amount = fields.Float(string="Balance Amount", compute='_compute_loan_amount')
        
#     total_paid_amount = fields.Float(
#         string="Total Paid Amount",
#         compute='_compute_loan_amount',

#     )


#     @api.multi
#     @api.depends('loan_lines.paid', 'loan_lines.paid_amount')
#     def _compute_loan_amount(self):
#         _logger.info('CALL Function')
#         for loan in self:
#             amount_paid = 0.0
#             for line in loan.loan_lines:
#                 amount_paid += line.paid_amount
#                 _logger.info("AMOUNT PAID ............")
#                 _logger.info(amount_paid)
#             loan.total_amount = loan.loan_amount
#             loan.paid_total = amount_paid
#             loan.balance_amount = loan.loan_amount - loan.paid_total
#             loan.total_paid_amount = amount_paid



# class InstallmentLine(models.Model):
#     _inherit = "hr.loan.line"
#     _description = "Installment Line"

#     @api.depends('input_line_ids', 'input_line_ids.amount')
#     def _compute_paid_amount(self):
#         for rec in self:
#             paid_total = 0.0
#             for line in rec.input_line_ids:
#                 paid_total += line.amount
#             rec.balanced_amount = rec.amount - paid_total
#             rec.paid_amount = paid_total
#             if rec.balanced_amount == 0.00:
#                 rec.paid = True
#             else:
#                 rec.paid = False

#     amount = fields.Float(
#         string="Amount", 
#         required=True
#     )

#     input_line_ids = fields.One2many(
#         string='Input Line',
#         comodel_name='hr.payslip.input',
#         inverse_name='loan_line_id',
#         domain=[('payslip_id.state', '=', 'done',)]
#     )
    
#     paid_amount = fields.Float(
#         string='Paid Amount',
#         compute='_compute_paid_amount'
#     )

#     balanced_amount = fields.Float(
#         string='Balanced Amount',
#         compute='_compute_paid_amount'
#     )

#     paid = fields.Boolean(
#         string="Paid",
#         compute='_compute_paid_amount'
#     )



# class HrPayslip(models.Model):
#     _inherit = 'hr.payslip'


#     def get_inputs(self, contract_ids, date_from, date_to):
#         """This Compute the other inputs to employee payslip.
#                            """
#         res = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)
#         contract_obj = self.env['hr.contract']
#         emp_id = self.employee_id
#         lon_obj = self.env['hr.loan'].search([('employee_id', '=', emp_id.id), ('state', '=', 'approve')])
#         l = []
#         for loan in lon_obj:
#             for loan_line in loan.loan_lines:
                
#                 monthloan = datetime.strptime(str(loan_line.date), '%Y-%m-%d').date()
#                 monthstart = datetime.strptime(str(date_from), '%Y-%m-%d').date()
#                 monthend = datetime.strptime(str(date_to), '%Y-%m-%d').date()

#                 if monthstart.month <= monthloan.month <= monthend.month and not loan_line.paid:

#                     if loan.payslip_cutoff == 0:
#                         loan.payslip_cutoff = 1
#                     res.append({
#                         'name': loan.loan_type_id.name + '/' + loan.name,
#                         'code':loan.loan_type_id.code, 'contract_id': self.contract_id.id,
#                         'amount' : loan_line.amount / loan.payslip_cutoff,
#                         'loan_line_id' : loan_line.id
#                     })
#         return res

#     @api.multi
#     def action_payslip_done(self):
#         for line in self.input_line_ids:
#             if line.loan_line_id:
#                 line.loan_line_id.loan_id._compute_loan_amount()
#         return super(HrPayslip, self).action_payslip_done()
