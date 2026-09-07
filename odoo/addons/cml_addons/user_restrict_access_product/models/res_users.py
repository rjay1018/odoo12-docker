# -*- coding: utf-8 -*-
##############################################################################
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 WebLine Apps 
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class res_users(models.Model):
    _inherit = 'res.users'
    
    allow_by = fields.Selection([('product', 'Product'), ('product_Category', 'Product Category'),('all', 'Product/Category')],
    default= 'product',string='Allow By')
    product_ids = fields.Many2many('product.template', string='Product')
    category_ids = fields.Many2many('product.category', string='Category')
	
    @api.multi
    @api.onchange('allow_by')
    def _onchange_allow(self):
    	for user in self:
    		user.category_ids = [(6, 0, [])]
    		user.product_ids = [(6, 0, [])]
	    		
    
