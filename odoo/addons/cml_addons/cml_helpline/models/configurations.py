# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CallType(models.Model):
    _name = 'call.type'
    _description = 'Call Type'

    _rec_name = 'name'
    _order = 'sequence ASC'

    name = fields.Char(
        string='Name',
        required=True,
        copy=False
    )
    
    sequence = fields.Integer(
        string='Sequence',
    )


class CallLanguage(models.Model):
    _name = 'call.language'
    _description = 'Call Language'

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Name',
        required=True,
        copy=False
    )

    sequence = fields.Integer(
        string='Sequence',
    )



class CaseCategory(models.Model):
    _name = 'case.category'
    
    # _inherits = {'client.support': 'name'}
    
    _description = 'Case Category'

    _rec_name = 'name'
    _order = 'name ASC'

    
    @api.multi
    @api.depends('name', 'client_support_id')
    def name_get(self):
        result = []
        for record in self:
            if record.client_support_id:
                name = '[' + record.client_support_id.name + '] ' + record.name
            else:
                name = record.name
            result.append((record.id, name))
        return result
    
    
    name = fields.Char(
        string='Name',
        required=True,
    )

    sequence = fields.Integer(
        string='Sequence',
    )
    
    description = fields.Text(
        string='Description',
    )
    
    client_support_id = fields.Many2one(
        string='Client Support',
        comodel_name='client.support',
    )

    helpline_session_id = fields.Many2one(
        string='Helpline Session',
        comodel_name='helpline.sessions',
        ondelete='cascade',
    )  



    

    
