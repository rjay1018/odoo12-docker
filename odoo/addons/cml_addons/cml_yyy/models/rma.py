from odoo import fields, models, api


class RmaMainYYY(models.Model):
    _name = 'rma.main'
    _inherit = ['rma.main','mail.thread']


    rma_note = fields.Html('RMA Note')
