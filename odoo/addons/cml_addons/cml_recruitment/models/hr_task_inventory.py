from odoo import models, fields, api


class JobFunctions(models.Model):
    _name = 'hr.job.funtions'
    _description = 'HR Job Functions Management'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('job.functions.sequence') or ('New')
        return super(JobFunctions, self).create(vals)

    name = fields.Char('Sequence', required=True, copy=False, readonly=True, index=True, default=lambda self: ('New'))
    task_id = fields.Many2one('project.task', ondelete='cascade', string='Task Inventory')
    result_area = fields.Text()
    performance_indicator = fields.Text()
    work_tools = fields.Text()
    monitoring = fields.Text('Monitoring and Evaluation')
    jobs_id = fields.Many2one('hr.job', 'Job Title', ondelete='cascade')
