# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class res_company(models.Model):
    _inherit = "res.company"

    # Global Search Document
    sh_global_document_search_is_enable = fields.Boolean(string='Enable global document search')
    
    sh_global_document_search_is_sale = fields.Boolean(string='Sale Order Search')

    sh_global_document_search_is_purchase = fields.Boolean(string='Purchase Order Search')

    sh_global_document_search_is_picking = fields.Boolean(string='Picking Order Search')

    sh_global_document_search_is_invoice = fields.Boolean(string='Invoice Order Search')

    sh_global_document_search_is_product = fields.Boolean(string='Product Search')

    sh_global_document_search_is_lot = fields.Boolean(string='Lots/Serial Number Search')

    sh_global_document_search_is_location = fields.Boolean(string='Location Search')

    sh_global_document_search_action_target_type = fields.Selection([
        ('current','Current'),
        ('new','New')
        ],default = 'current' ,string='Document Open Mode', translate=True)
        
    
        
        
        
    #sale
    sh_sale_barcode_scanner_type = fields.Selection([
        ('int_ref','Internal Reference'),
        ('barcode','Barcode'),
        ('sh_qr_code','QR Code'),
        ('all','All'),
        ],default = 'barcode' ,string='Product Scan Options', translate=True)
    
    
    sh_sale_barcode_scanner_last_scanned_color = fields.Boolean(
        string='Last scanned Color?', translate=True)

    sh_sale_barcode_scanner_move_to_top = fields.Boolean(
        string='Last scanned Move To Top?', translate=True)

    sh_sale_barcode_scanner_warn_sound = fields.Boolean(
        string='Warning Sound?', translate=True)
    
    sh_sale_barcode_scanner_auto_close_popup = fields.Integer(
        string='Auto close alert/error message after', translate=True)

    #purchase
    sh_purchase_barcode_scanner_type = fields.Selection([
        ('int_ref','Internal Reference'),
        ('barcode','Barcode'),
        ('sh_qr_code','QR Code'),('all','All'),
        ],default = 'barcode' ,string='Product Scan Options', translate=True)
    
    sh_purchase_barcode_scanner_last_scanned_color = fields.Boolean(
        string='Last scanned Color?', translate=True)

    sh_purchase_barcode_scanner_move_to_top = fields.Boolean(
        string='Last scanned Move To Top?', translate=True)

    sh_purchase_barcode_scanner_warn_sound = fields.Boolean(
        string='Warning Sound?', translate=True)    
    
    sh_purchase_barcode_scanner_auto_close_popup = fields.Integer(
        string='Auto close alert/error message after', translate=True)   
    
        

    #stock picking
    sh_inventory_barcode_scanner_type = fields.Selection([
        ('int_ref','Internal Reference'),
        ('barcode','Barcode'),
        ('sh_qr_code','QR Code'),
        ('all','All'),
        ],default = 'barcode' ,string='Product Scan Options', translate=True)

    sh_inventory_barcode_scanner_is_add_product = fields.Boolean(string = "Is add new product in picking?",translate=True) 


    sh_inventory_barcode_scanner_last_scanned_color = fields.Boolean(
        string='Last scanned Color?', translate=True)

    sh_inventory_barcode_scanner_move_to_top = fields.Boolean(
        string='Last scanned Move To Top?', translate=True)

    sh_inventory_barcode_scanner_warn_sound = fields.Boolean(
        string='Warning Sound?', translate=True)  
    
    
    sh_inventory_barcode_scanner_auto_close_popup = fields.Integer(
        string='Auto close alert/error message after', translate=True)      
    
    
    #inventory adjustment
    sh_inven_adjt_barcode_scanner_type = fields.Selection([
        ('int_ref','Internal Reference'),
        ('barcode','Barcode'),
        ('sh_qr_code','QR Code'),
        ('all','All'),
        ],default = 'barcode' ,string='Product Scan Options', translate=True)
    
    
    sh_inven_adjt_barcode_scanner_last_scanned_color = fields.Boolean(
        string='Last scanned Color?', translate=True)

    sh_inven_adjt_barcode_scanner_move_to_top = fields.Boolean(
        string='Last scanned Move To Top?', translate=True)

    sh_inven_adjt_barcode_scanner_warn_sound = fields.Boolean(
        string='Warning Sound?', translate=True)  
    
        
    sh_inven_adjt_barcode_scanner_auto_close_popup = fields.Integer(
        string='Auto close alert/error message after', translate=True)   
    
            
    
    #invoice
    sh_invoice_barcode_scanner_type = fields.Selection([
        ('int_ref','Internal Reference'),
        ('barcode','Barcode'),
        ('sh_qr_code','QR Code'),
        ('all','All'),
        ],default = 'barcode' ,string='Product Scan Options', translate=True)
    
    sh_invoice_barcode_scanner_last_scanned_color = fields.Boolean(
        string='Last scanned Color?', translate=True,readonly = False)

    sh_invoice_barcode_scanner_move_to_top = fields.Boolean(
        string='Last scanned Move To Top?', translate=True,readonly = False)

    sh_invoice_barcode_scanner_warn_sound = fields.Boolean(
        string='Warning Sound?', translate=True,readonly = False)      
    
    sh_invoice_barcode_scanner_auto_close_popup = fields.Integer(
        string='Auto close alert/error message after', translate=True,readonly = False)        
    
    
    
    

    #BOM
    sh_bom_barcode_scanner_type = fields.Selection([
        ('int_ref','Internal Reference'),
        ('barcode','Barcode'),
        ('sh_qr_code','QR Code'),
        ('all','All'),
        ],default = 'barcode' ,string='Product Scan Options', translate=True)
    
    sh_bom_barcode_scanner_last_scanned_color = fields.Boolean(
        string='Last scanned Color?', translate=True,readonly = False)

    sh_bom_barcode_scanner_move_to_top = fields.Boolean(
        string='Last scanned Move To Top?', translate=True,readonly = False)

    sh_bom_barcode_scanner_warn_sound = fields.Boolean(
        string='Warning Sound?', translate=True,readonly = False)     
    

    sh_bom_barcode_scanner_auto_close_popup = fields.Integer(
        string='Auto close alert/error message after', translate=True,readonly = False)   

    #scrap
    sh_scrap_barcode_scanner_type = fields.Selection([
        ('int_ref','Internal Reference'),
        ('barcode','Barcode'),
        ('sh_qr_code','QR Code'),('all','All'),
        ],default = 'barcode', string='Product Scan Options', translate=True)
    
    sh_scrap_barcode_scanner_warn_sound = fields.Boolean(
        string='Warning Sound?', translate=True,readonly = False)      
    
    sh_scrap_barcode_scanner_auto_close_popup = fields.Integer(
        string='Auto close alert/error message after', translate=True,readonly = False)  
