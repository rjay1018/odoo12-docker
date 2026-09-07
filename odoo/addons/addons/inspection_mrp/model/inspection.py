from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

class Inspection(models.Model):
    _name = 'inspection'
    _description = 'Finished Goods Inspection'
    
    name = fields.Char('Name',required=True)
    type = fields.Selection([('descriptive','Descriptive'),('image','Image'),('numeric','Numeric Type')],default="descriptive")
    max_value = fields.Float('Max Value')
    min_value = fields.Float('Min Value')
    image = fields.Binary()
    description = fields.Char('Description')
    product_id = fields.Many2one('product.product','Product',domain="[('bom_ids','!=',False)]",required=True)

    @api.onchange('min_value','max_value')
    def onchange_min_max(self):
        if self.min_value:
            if self.max_value < self.min_value:
                raise ValidationError('Max value should be greater than Min Value')
        if self.max_value:
            if self.min_value > self.max_value:
                raise ValidationError('Min Value should be less than Max Value')


class QualityInspection(models.Model):
    _name = 'quality.inspection'
    _description = 'Quality Inspection'
    
    @api.model
    def create(self,vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('quality.inspection') or _('New')
        return super(QualityInspection,self).create(vals)  
    
    _sql_constraints = [
        ('Stock_unique', 'unique(stock_line_id)', "Inspection is already created for this Goods."),
    ]
    
    name = fields.Char('Name')
    stock_line_id = fields.Many2one('stock.move.line','Stock',required=True)
    product_id = fields.Many2one('product.product','Product',required=True)
    inspect_ids = fields.One2many('quality.inspection.line','inspect_id')
    state = fields.Selection([('draft','Draft'),('partial','Partial'),('pass','Pass'),('fail','Fail')],'Status',copy=False,default='draft')
    
    def chg_done(self):
        self.stock_line_id.inspect_id = self.id
        self.state = "pass"
        
    def chg_fail(self):
        self.stock_line_id.inspect_id = self.id
        self.state = 'fail'
        
class QualityInspectLine(models.Model):
    _name = 'quality.inspection.line'

    inspect_id = fields.Many2one('quality.inspection','Quality Inspection')
    product_id = fields.Many2one('product.product','Product')
    inspection_id = fields.Many2one('inspection','Inspection',domain="[('product_id','=',product_id)]",required=True)
    type = fields.Selection([('descriptive','Descriptive'),('image','Image'),('numeric','Numeric Type')])
    max_value = fields.Float('Max Value')
    min_value = fields.Float('Min Value')
    image = fields.Binary()
    inspect_value = fields.Float('Inspect Value')
    description = fields.Char('Description')
    test = fields.Selection([('yes','Yes'),('no','No')],'Test',default='yes')
    remarks = fields.Text('Remarks')
    
    
    
class StockLine(models.Model):
    _inherit = 'stock.move.line'
    
    inspect_id = fields.Many2one('quality.inspection','Inspection') 
    
    def quality_inspection(self):
        for rec in self:
#             print(rec.parent_id,'kkk')
            quality = self.env['quality.inspection'].search([('stock_line_id','=',rec.id)])
            if quality:
                raise ValidationError("Already Inspection Completed")
            if rec.product_id.bom_ids:
                inspection_line = []
                if rec:
                    inspection = self.env['inspection'].search([])
                    if not inspection:
                        raise ValidationError('Inspection not found. Create Inspection for this Product..!!')
                    for inspect in inspection:
                        if rec.product_id.id == inspect.product_id.id:
                            inspection_line.append((0,0,{'product_id':inspect.product_id.id,'inspection_id':inspect.id,
                                                        'type':inspect.type,'max_value':inspect.max_value,'min_value':inspect.min_value,
                                                        'image':inspect.image,'description':inspect.description}))
                    return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'quality.inspection',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'views': [[self.env.ref('inspection_mrp.view_quality_inspection_form').id, 'form']],
                    'target': 'new',
                    'context':{
                        'default_stock_line_id':rec.id,
                        'default_product_id':rec.product_id.id,
                        'default_inspect_ids':inspection_line,
                        }
                }
    def quality_inpected(self):
        return {
                'type': 'ir.actions.act_window',
                'res_model': 'quality.inspection',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': self.inspect_id.id,
                'target': 'new',
                }
    
class Production(models.Model):
    _inherit = 'mrp.production'
    
    is_quality_inspected = fields.Boolean('Quality Inspected',compute='onchange_quality_inspected',default=False)
    is_quality_pass = fields.Boolean('Quality Pass',compute="onchange_quality_inspected",default=False)
    
    @api.depends('finished_move_line_ids.inspect_id')
    def onchange_quality_inspected(self):
        count = 0
        true_count = 0
        false_count = 0
        for rec in self.finished_move_line_ids:
            count += 1
            if rec.inspect_id:
                if rec.inspect_id.state == 'pass':
                    self.is_quality_pass = True
            if rec.inspect_id.id != False:
                true_count += 1
            elif rec.inspect_id.id == False:
                false_count += 1
        if count == true_count:
            self.is_quality_inspected = True
            
    @api.multi
    def button_mark_done(self):
        for rec in self:
            if rec.is_quality_pass == False:
                return {
                'type': 'ir.actions.act_window',
                'res_model': 'mrp.wizard',
                'view_type': 'form',
                'view_mode': 'form',
                'views': [[self.env.ref('inspection_mrp.mrp_wizard_view_form').id, 'form']],
                'target': 'new',
                'context':{
                        'default_production_id':rec.id,
                        }
                }
        return super(Production,self).button_mark_done()
        
    