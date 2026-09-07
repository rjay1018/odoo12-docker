import datetime
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
date_format = "%Y-%m-%d"

AVAILABLE_PRIORITIES = [
    ('0', 'Poor'),
    ('1', 'Fair'),
    ('2', 'Good'),
    ('3', 'Very Good'),
    ('4', 'Excellent'),
]
class Discplinary_additional(models.Model):
    _inherit = 'disciplinary.action'
    date_violation=fields.Date(string="Date of Violation")
    date_issued=fields.Date(string="Date Issued")
    name=fields.Char(string='Reference', required=True, copy=False, readonly=True,
                       default=lambda self: _('Pink Slip'))
    department_name = fields.Many2one('hr.department', string='SATO/UNIT/CLUSTER/SECTOR', required=True)
    discipline_reason = fields.Many2one('discipline.category', string='Violation', required=True)
    note = fields.Text(string="Recommendation")

    position=fields.Char(sttring="Position")

class Reesignation_additional(models.Model):
    _inherit = 'hr.resignation'
    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('Resignation'))
    department_id = fields.Many2one('hr.department', string="SATO/UNIT/CLUSTER/SECTOR", related='employee_id.department_id',
                                    help='Department of the employee')
    joined_date = fields.Date(string='Date Hired', required=True,
                              help='Joining date of the employee')
    resign_confirm_date = fields.Date(string="Effectivity Date of Resignation", help='Date on which the request is confirmed')
    expected_revealing_date = fields.Date(string="Separation Date", required=True,
                                          help='Date on which he is revealing from the company')
    position=fields.Char(sttring="Position")
    employee_status = fields.Selection([
        ('trainee', 'Trainee'),
        ('propitionary', 'Probitionary'),
        ('regular', 'Regular'),
        ('regular_no', 'Regular No Earnings'),
        ('project', 'Project Base'),
        ('separated_f', 'Separated Failed'),
        ('separated_l', 'Separated Leave'),
        ('separated_d', 'Separated Deceased'),
        ('separated_t', 'Separated Terminated')
        ], string="Employment Status")
    filing_date=fields.Date(string="Filing Date")

class Employee_additional(models.Model):
    _inherit = 'hr.employee'

    training_seminar_ids=fields.One2many('employee.training.seminar.table', 'employee_id', string="Training/Seminar")

    discipline_count = fields.Integer(compute='_compute_discipline_count', string='Discipline')


    def _compute_discipline_count(self):
        # read_group as sudo, since contract count is displayed on form view
        contract_data = self.env['disciplinary.action'].sudo().read_group([('employee_name', 'in', self.ids)], ['employee_name'], ['employee_name'])
        result = dict((data['employee_name'][0], data['employee_name_count']) for data in contract_data)
        for employee in self:
            employee.discipline_count = result.get(employee.id, 0)


class HrEmployeeContractName_additional(models.Model):
    """This class is to add emergency contact table"""

    _inherit = 'hr.emergency.contact'
    relation = fields.Char(string='Name of the Contact Person')
    number = fields.Char(string='Contact Number', help='Contact Number')
    relationship=fields.Char(string='Relationship', help='Relation with employee')

class Employee_orientation_change(models.Model):
    _inherit = 'employee.orientation'
    name = fields.Char(string='Employee Orientation', readonly=True, default=lambda self: _('New Employee Orientation Schedule'))
    date = fields.Date(string="Inclusive Date", default=fields.Datetime.now)
    responsible_user = fields.Many2one('res.users', string='Training in Charge')
    # employee_company = fields.Many2one('res.company', string='KSO', required=True,
    #                                    default=lambda self: self.env.user.company_id)
    department = fields.Many2one('hr.department', string='SATO/UNIT', related='employee_name.department_id', required=True)

class Employee_orientation_change_checklist(models.Model):
    _inherit = 'checklist.line'
    line_name = fields.Char(string='Orientation Module', required=True)
    responsible_user = fields.Many2one('res.users', string='Training in Charge', required=True)

class OrientationChecklist_inherit(models.Model):
    _inherit = 'orientation.checklist'

    checklist_name = fields.Char(string='Orientation Module', required=True)
    checklist_department = fields.Many2one('hr.department', string='SATO/UNIT', required=True)

class EmployeeTraining_changes(models.Model):
    _inherit = 'employee.training'

    program_name = fields.Char(string='Training/Seminar Program', required=True)
    program_department = fields.Many2one('hr.department', string='SATO/UNIT/CLUSTER', required=True)
    program_convener = fields.Many2one('res.users', string='Employee', size=32, required=True)
    training_id = fields.One2many('hr.employee', string='Employee Details', compute="employee_details")

class Employeeapplicant_changes_hris(models.Model):
    _inherit = 'hr.applicant'
    priority = fields.Selection(AVAILABLE_PRIORITIES, string="Interview Rate", default='0')
    department_id = fields.Many2one('hr.department', string="SATO/UNIT/CLUSTER/SECTOR")

class Employeecontract_changes_hris(models.Model):
    _inherit = 'hr.contract'

    department_id = fields.Many2one('hr.department', string="SATO/UNIT/CLUSTER/SECTOR")
    wage = fields.Monetary(string='Basic Pay', track_visibility='onchange')
    travel_reimbursement_amount = fields.Monetary(string='ECOLA',
                                               track_visibility='onchange',
                                               readonly=True,
                                               states={'draft': [('readonly', False)]},
                                               help='The Reimbursement of travel expenses for the employee')
    phone_reimbursement_amount = fields.Monetary('Communication Allowance',
                                              track_visibility='onchange',
                                              readonly=True,
                                              states={'draft': [('readonly', False)]},
                                              help='The Reimbursement of phone expenses for the employee')
    meal_allowance = fields.Monetary('Rice Subsidy',
                                  track_visibility='onchange',
                                  readonly=True,
                                  states={'draft': [('readonly', False)]},
                                  help='The Meal Allowance of the employee')
    moving_allowance = fields.Monetary('Relocation Allowance',
                                    track_visibility='onchange',
                                    readonly=True,
                                    states={'draft': [('readonly', False)]},
                                    help='The Moving Allowance (e.g. gasoline compensation, bus expense, etc) for the employee')
    harmful_subsidies = fields.Monetary('Medicine Allowance',
                                     track_visibility='onchange',
                                     readonly=True,
                                          states={'draft': [('readonly', False)]},
                                     help='The Harmful Subsidies for the employee')
    trial_date_end=fields.Date(string='End of Training/Probationary Period')


class HrEmployeeTraining_additionalTable(models.Model):
    _name = 'employee.training.seminar.table'
    employee_id=fields.Many2one('hr.employee', string="Employee", required="True")
    training_seminar_id=fields.Many2one('employee.training.seminar',string="Training/Seminar", required="True")
    venue_id=fields.Many2one('employee.training.venue',string="Venue")
    date=fields.Date(string="Inclusive Date")
    provider=fields.Many2one('employee.training.provider', string="Provider")

class HrEmployeeTraining_additional(models.Model):
    _name = 'employee.training.seminar'
    name=fields.Char(string='Training/Seminar')
class HrEmployeeTraining_venue(models.Model):
    _name = 'employee.training.venue'
    name=fields.Char(string='Venue')
class HrEmployeeTraining_provider(models.Model):
    _name = 'employee.training.provider'
    name=fields.Char(string='Venue')

class HrEmployeeTransfer_additional(models.Model):
    _inherit = 'employee.transfer'
    supervisor = fields.Many2one('employee.transfer.supervisor', string='Immediate Supervisor/Manager')
    kso = fields.Many2one('employee.transfer.kso', string='KSO')
    date_started=fields.Date(string="Date Started")
    date_transfer=fields.Date(string="Date of Transfer")
    department_id = fields.Many2one('hr.department', string="SATO/UNIT", related='employee_id.department_id',
                                    help='Department of the employee')

class HrEmployeeTransfer_additionalsupervisor(models.Model):
    _name = 'employee.transfer.supervisor'
    name=fields.Char(string='Immediate Supervisor/Manager')
class HrEmployeeTransfer_additionalkso(models.Model):
    _name = 'employee.transfer.kso'
    name=fields.Char(string='KSO')
