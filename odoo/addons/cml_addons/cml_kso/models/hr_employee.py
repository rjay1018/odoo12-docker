from odoo import models, fields, api
from dateutil.relativedelta import relativedelta



class EmployeeKSO(models.Model):
    _inherit = 'hr.employee'
    
    address_id = fields.Many2one(
        'res.partner',
        'Organization'
    )
    
    # work_location = fields.Char(
    #     string='Satellite Office/Unit',
    # )
    
    department_id = fields.Many2one(
        'hr.department',
        'Cluster/Sector',
    )
    
    parent_id = fields.Many2one(
        'hr.employee',
        'Immediate Supervisor/Manager'
    )
    
    # middlename = fields.Char(
    #     string='Middle Name',
    # )
    
    kfamily_id = fields.Many2one(
        'hr.kfamily',
        string='K-Family'
    )

    sector_id = fields.Many2one(
        'hr.sector',
        string='Sector'
    )

    cluster_id = fields.Many2one(
        'hr.cluster',
        string='Sector'
    )

    unit_id = fields.Many2one(
        'hr.unit',
        string='Unit/Sato'
    )

    yrsofservice = fields.Integer(
        string='Years in Service', 
        readonly=True, 
        store=True,
        compute='_compute_yos',

    )
    @api.multi
    @api.depends("joining_date")
    def _compute_yos(self):
        for record in self:
            yos = 0
            if record.joining_date:
                yos = relativedelta(
                    fields.Date.today(),
                    record.joining_date,
                ).years
            record.yrsofservice = yos



############ KSO Grouping ################


class HrKfamily(models.Model):
    _name = 'hr.kfamily'
    _description = "K-Family"
    _order = 'name'

    name = fields.Char('Name', required=True)

class HrSector(models.Model):
    _name = 'hr.sector'
    _description = "Sector"
    _order = 'name'

    name = fields.Char('Name', required=True)

class HrCluster(models.Model):
    _name = 'hr.cluster'
    _description = "Sector"
    _order = 'name'

    name = fields.Char('Name', required=True)

class HrUnit(models.Model):
    _name = 'hr.unit'
    _description = "Unit"
    _order = 'name'

    name = fields.Char('Name', required=True)