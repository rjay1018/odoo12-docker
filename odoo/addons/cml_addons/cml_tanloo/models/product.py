from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_department_id = fields.Many2one(
        'product.department',
        string='Department'
    )

    product_section_id = fields.Many2one(
        'product.section',
        string='Section'
    )

    product_division_id = fields.Many2one(
        'product.division',
        string='Division'
    )

    product_model = fields.Char(
        string='Model',
    )


class ProductDepartment(models.Model):
    _name = 'product.department'
    _description = "Product Department"
    _order = 'name'

    name = fields.Char('Name', required=True)
    product_ids = fields.One2many(
        'product.template',
        'product_department_id',
        string='Department',
    )


class ProductSection(models.Model):
    _name = 'product.section'
    _description = "Product Section"
    _order = 'name'

    name = fields.Char('Name', required=True)
    product_ids = fields.One2many(
        'product.template',
        'product_section_id',
        string='Section',
    )

class ProductDivision(models.Model):
    _name = 'product.division'
    _description = "Product Division"
    _order = 'name'

    name = fields.Char('Name', required=True)
    product_ids = fields.One2many(
        'product.template',
        'product_division_id',
        string='Division',
    )