from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Partner(models.Model):
    _inherit = "res.partner"

    partner_categ_comm_ids = fields.One2many('partner.category.commission', 'partner_id')
    product_categ_comm_ids = fields.One2many('product.category.commission', 'partner_id')
    agent_partner_categ_ids = fields.One2many('partner.category.commission', 'agent_id')
    agent_product_categ_ids = fields.One2many('product.category.commission', 'agent_id')
    quota_ids = fields.One2many('sale.commission.agent.quota', 'agent_id', string='Product Quotas')
    commission_type = fields.Selection(related='commission.commission_type', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        partners = super(Partner, self).create(vals_list)
        if not (
            self.env.context.get('install_mode')
            or self.env.context.get('skip_customer_commission_check')
        ):
            for partner in partners:
                if partner.customer and not partner.agent and not partner.parent_id:
                    has_valid_comm = any(
                        line.agent_id and line.commission_id
                        for line in partner.partner_categ_comm_ids
                    )
                    if not has_valid_comm:
                        raise ValidationError(_(
                            "Sales Agent and Commission Type are required when creating a new customer. "
                            "Please add at least one line under the 'Sales Commission' tab."
                        ))
        return partners


class Users(models.Model):
    _inherit = "res.users"

    @api.model_create_multi
    def create(self, vals_list):
        return super(Users, self.with_context(skip_customer_commission_check=True)).create(vals_list)


class SaleCommissionAgentQuota(models.Model):
    _name = 'sale.commission.agent.quota'
    _description = 'Sales Agent Product Quota'
    _order = 'product_id'

    agent_id = fields.Many2one('res.partner', 'Sales Agent', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Product', required=True)
    quota_qty = fields.Float('Quota Qty', required=True)

    @api.multi
    @api.constrains('agent_id', 'product_id')
    def _check_duplicate_product(self):
        for rec in self:
            domain = [
                ('agent_id', '=', rec.agent_id.id),
                ('product_id', '=', rec.product_id.id),
            ]
            if self.search_count(domain) > 1:
                raise ValidationError(_('Duplicate product quota exists for this sales agent.'))



class PartnerCategoryCommission(models.Model):
    _name = 'partner.category.commission'

    partner_id = fields.Many2one('res.partner', 'Customer', ondelete='cascade')
    agent_id = fields.Many2one('res.partner', 'Agent', required=True, ondelete='cascade')
    commission_id = fields.Many2one('sale.commission', 'Commission Type', required=True)

    @api.onchange('partner_id')
    def onchange_partner(self):
        self.commission_id = None
        ctx = dict(self._context)
        if 'partner_categ' in ctx:
            if ctx['comm_type'] != 'fix':
                self.commission_id = ctx['comm_id']
        elif 'product_categ' in ctx:
            if ctx['comm_type'] == 'fix':
                self.commission_id = ctx['comm_id']
        else:
            if self.partner_id.commission.commission_type != 'fix':
                self.commission_id = self.agent_id.commission

    @api.onchange('agent_id')
    def onchange_agent(self):
        self.commission_id = self.agent_id.commission

    @api.multi
    @api.constrains('partner_id', 'agent_id')
    def _check_duplicate_agent(self):
        for obj in self:
            args = [
                ('partner_id', '=', obj.partner_id.id),
                ('agent_id', '=', obj.agent_id.id)
            ]
            if len(obj.search(args)) > 1:
                raise ValidationError(_('Duplicate sales agent exists'))


class ProductCategoryCommission(models.Model):
    _inherit = 'partner.category.commission'
    _name = 'product.category.commission'

    categ_id = fields.Many2one('product.category', 'Category', required=True)

    @api.multi
    @api.constrains('partner_id', 'agent_id')
    def _check_duplicate_agent(self):
        for obj in self:
            if obj.categ_id:
                args = [
                    ('categ_id', '=', obj.categ_id.id),
                    ('partner_id', '=', obj.partner_id.id),
                    ('agent_id', '=', obj.agent_id.id)
                ]
                if len(obj.search(args)) > 1:
                    raise ValidationError(_('Duplicate product category for an agent exists'))
