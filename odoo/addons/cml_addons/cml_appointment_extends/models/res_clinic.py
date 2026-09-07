from odoo import models, fields, api


class ResClinic(models.Model):
    _name = 'res.clinic'
    _description = 'clinic'

    name = fields.Char(
        required=True,
        string="Name"
    )
    street = fields.Char(
        string="Street"
    )
    street2 = fields.Char(
        string="Street2"
    )
    city = fields.Char(
        string="City"
    )
    state_id = fields.Many2one(
        'res.country.state',
        string="State"
    )
    zip = fields.Char(
        string="Zip"
    )
    country_id = fields.Many2one(
        'res.country',
        string="Country"
    )
    mobile = fields.Char(
        string="Mobile"
    )
    email = fields.Char(
        string="Email"
    )
