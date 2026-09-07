# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class QualityHazard(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = "quality.hazard"
    _description = "Hazard"

    name = fields.Char("Name", required=True)
    
class QualityLikelihood(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = "quality.likelihood"
    _description = "Likelihood"

    name = fields.Char("Name", required=True)
    
class QualitySeverity(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = "quality.severity"
    _description = "Severity"

    name = fields.Char("Name", required=True)
    
class QualityRating(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = "quality.rating"
    _description = "Rating"

    name = fields.Char("Name", required=True)
    
class QualityRoutingWorkcenter(models.Model):
    _name = "quality.routing.workcenter"
    _rec_name = "operation_name"
    
    operation_name = fields.Char('Operation')
    workcenter_id = fields.Many2one('mrp.workcenter', 'Workcenter')
    allow_quality_check = fields.Boolean('Allow Quality Check')
    product_id = fields.Many2one('product.product','Product')
    qc_point_id = fields.Many2one('sh.qc.point', 'Quality Point')
    
class ShQcPoint(models.Model):
    _inherit = "sh.qc.point"

    hazard_id = fields.Many2one("quality.hazard", "Hazard")
    likelihood_id = fields.Many2one("quality.likelihood", "Likelihood")
    severity_id = fields.Many2one("quality.severity", "Severity")
    rating_id = fields.Many2one("quality.rating", "Rating")
    routing_workcenter_ids = fields.One2many('quality.routing.workcenter', 'qc_point_id', 'Routing Workcenter')
    
    def get_routing_operation(self):
        bom_id = self.env['mrp.bom'].search(['|',('product_id','=',self.product_id.id),('product_tmpl_id','=',self.product_id.product_tmpl_id.id)], limit=1)
        if bom_id and bom_id.routing_id:
            for operation in bom_id.routing_id.operation_ids:
                qc_routing_wc = self.env['quality.routing.workcenter']
                qcr_wc_vals = {
                    'qc_point_id': self.id, 
                    'allow_quality_check': False,
                    'product_id': self.product_id.id,
                    'operation_name': operation.name,
                    'workcenter_id': operation.workcenter_id.id
                }
                domain = [
                    ('qc_point_id', '=', self.id),('product_id', '=', self.product_id.id),
                    ('operation_name', '=', operation.name),('workcenter_id', '=', operation.workcenter_id.id)
                ]
                qc_rwc_ids = qc_routing_wc.search(domain)
                print ("\n\nqc_rwc_ids",qc_rwc_ids)
                if not qc_rwc_ids:
                    qc_routing_wc.sudo().create(qcr_wc_vals)
        return True
        
        
class MRPWorkorder(models.Model):
    _inherit = "mrp.workorder"
    
    def read(self, fields=None, load='_classic_read'):
        result = super(MRPWorkorder, self).read(fields=fields, load=load)
        for mw in self:
            qc_routing_wc = self.env['quality.routing.workcenter']
            if mw.name and mw.workcenter_id:
                domain = [
                    ('operation_name', '=', mw.name),
                    ('workcenter_id', '=', mw.workcenter_id.id),
                    ('product_id', '=', mw.product_id.id),
                    ('allow_quality_check', '=', True)
                ]
                qc_routing_wc_id = qc_routing_wc.search(domain)
                if qc_routing_wc_id:
                    self.env.cr.execute("""UPDATE mrp_workorder SET allow_quality_check=True where id=%s""", (mw.id,))
                
        return result
    
        
    allow_quality_check = fields.Boolean(string='Allow Quality Check')



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
