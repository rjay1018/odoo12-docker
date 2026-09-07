# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError

class MRPWizard(models.TransientModel):
    
    _name = 'mrp.wizard'
    
    name = fields.Char('Name')
    production_id = fields.Many2one('mrp.production','Production')
    
    def do_stock(self):
        self.production_id.ensure_one()
        for wo in self.production_id.workorder_ids:
            if wo.time_ids.filtered(lambda x: (not x.date_end) and (x.loss_type in ('productive', 'performance'))):
                raise UserError(_('Work order %s is still running') % wo.name)
        self.production_id._check_lots()

        self.production_id.post_inventory()
        # Moves without quantity done are not posted => set them as done instead of canceling. In
        # case the user edits the MO later on and sets some consumed quantity on those, we do not
        # want the move lines to be canceled.
        (self.production_id.move_raw_ids | self.production_id.move_finished_ids).filtered(lambda x: x.state not in ('done', 'cancel')).write({
            'state': 'done',
            'product_uom_qty': 0.0,
        })
        self.production_id.write({'state': 'done', 'date_finished': fields.Datetime.now()})
        return self.production_id.write({'state': 'done'})
    
    def do_scrap(self):
        self.production_id.ensure_one()
        return {
            'name': _('Scrap'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.scrap',
            'view_id': self.env.ref('stock.stock_scrap_form_view2').id,
            'type': 'ir.actions.act_window',
            'context': {'default_production_id': self.production_id.id,
                        'product_ids': (self.production_id.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel')) | self.production_id.move_finished_ids.filtered(lambda x: x.state == 'done')).mapped('product_id').ids,
                        },
            'target': 'new',
        }
#         self.production_id.button_scrap()