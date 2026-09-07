from odoo import models, fields, api


class HrCompetency(models.Model):
    """ Competency Profile"""

    _name = 'hr.competency'
    _description = 'HR Competency Management'
    _order = 'name'

    SKILL_LEVEL = [
        ('1', 'Level 1'),
        ('2', 'Level 2'),
        ('3', 'Level 3'),
        ('4', 'Level 4'),
        ('5', 'Level 5'),
        ('6', 'Level 6'),
        ('7', 'Level 7')
    ]

    name = fields.Char(translate=True)
    knowledge = fields.Text('Knowledge Base')
    capability = fields.Text('Capability Requirements')
    talent = fields.Text(string='Talent Requirements')
    skill_level = fields.Selection(SKILL_LEVEL)
    org_result = fields.Text('Organizational Result Area')
    jobs_id = fields.Many2one('hr.job', 'Job Title')
