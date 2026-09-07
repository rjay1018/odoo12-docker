# Copyright YEAR(S), AUTHOR(S)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models

class PostEvaluation(models.Model):
    
    _name = 'post.evaluation'
    _description = u'Post Evaluation'

    _rec_name = 'name'
    _order = 'name ASC'

    @api.model
    def create(self, vals):
        if vals.get('sequence', ('New')) == ('New'):
            vals['sequence'] = self.env['ir.sequence'].next_by_code('post.evaluation.sequence') or ('New')
        result = super(PostEvaluation, self).create(vals)
        return result

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=True,
        default=lambda self: ('New')
    )

