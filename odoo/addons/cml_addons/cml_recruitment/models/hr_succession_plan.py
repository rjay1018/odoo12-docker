from odoo import models, fields, api


class SuccessionPlan(models.Model):
    _name = 'succession.plan'
    _description = 'Succession Planning'
    _rec_name = 'candidate_id'
    _order = 'ranking'

    RANKING = [
        ('0', "0"),
        ('1', "1"),
        ('2', "2"),
        ('3', "3")
    ]

    READINESS = [
        ('rdnw', 'Ready Now'),
        ('rdly', 'Less than one year'),
        ('rd12', '1 to 2 years readiness'),
        ('rd34', '3 to 4 years readiness'),
        ('rdnr', 'Not Ready')
    ]

    candidate_id = fields.Many2one('hr.employee', 'Candidate Name', required=True)

    ################NINEBOX FEATURES TO DO#################
    potential = fields.Selection(related='candidate_id.potential')
    performance = fields.Selection(related='candidate_id.performance')
    nbox_rating = fields.Char('Nine Box Rating', readonly=True)
    ################NINEBOX FEATURES TO END#################

    job_title = fields.Char(related='candidate_id.job_title', store=True)
    interim_successor = fields.Boolean()
    candidate_since = fields.Date()
    ranking = fields.Selection(RANKING)
    readiness = fields.Selection(READINESS, required=True)
    jobs_id = fields.Many2one('hr.job', 'Job Position', ondelete='cascade', readonly=True)
