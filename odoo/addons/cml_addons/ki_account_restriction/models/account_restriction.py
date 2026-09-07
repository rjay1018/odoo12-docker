# from odoo.osv import expression
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    user_restriction = fields.Boolean(string="User Restriction")
    user_restriction_ids = fields.One2many('user.restriction.account', 'relations_id')

    # @api.model
    # def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
    #     login = self.env.user.ids
    #     domain = ['|', ('user_restriction', '=', False), ('user_restriction_ids.user_id', 'in', login)]
    #     args += domain
    #     print("===== args", args)
    #     return super(AccountJournal, self)._search(args, offset, limit, order, count, access_rights_uid)


class AccountRestriction(models.Model):
    _name = "user.restriction.account"

    relations_id = fields.Many2one('account.journal')
    user_id = fields.Many2one('res.users', string="User", required=True)
    allow_create = fields.Boolean(string="Create")
    allow_validate = fields.Boolean(string="Validate")


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.multi
    def action_post(self):
        if self.journal_id:
            if self.journal_id.user_restriction:
                login = self.env.user.id
                line = self.journal_id.user_restriction_ids.filtered(lambda x: x.user_id.id == login)
                if line:
                    if not line.allow_validate:
                        raise ValidationError(_("Sorry You Don't Have Permission To Validate!"))
                else:
                    raise ValidationError(_("Sorry You Don't Have Permission To Validate!"))
        return super(AccountMove, self).action_post()


    @api.model
    def create(self, vals_list):
        res = super(AccountMove, self).create(vals_list)
        if res.journal_id:
            if res.journal_id.user_restriction:
                login = res.env.user.id
                line = res.journal_id.user_restriction_ids.filtered(lambda x: x.user_id.id == login)
                if line:
                    if not line.allow_create:
                        raise ValidationError(_("Sorry You Don't Have Permission To Create!"))
                else:
                    raise ValidationError(_("Sorry You Don't Have Permission To Create!"))
        return res


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def create(self, vals):
        res = super(AccountInvoice, self).create(vals)
        if res.journal_id:
            if res.journal_id.user_restriction:
                login = res.env.user.id
                line = res.journal_id.user_restriction_ids.filtered(lambda x: x.user_id.id == login)
                if line:
                    if not line.allow_create:
                        raise ValidationError(_("Sorry You Don't Have Permission To Create!"))
                else:
                    raise ValidationError(_("Sorry You Don't Have Permission To Create!"))
        return res

    @api.multi
    def action_invoice_open(self):
        if self.journal_id:
            if self.journal_id.user_restriction:
                login = self.env.user.id
                line = self.journal_id.user_restriction_ids.filtered(lambda x: x.user_id.id == login)
                if line:
                    if not line.allow_validate:
                        raise ValidationError(_("Sorry You Don't Have Permission To Validate!"))
                else:
                    raise ValidationError(_("Sorry You Don't Have Permission To Validate!"))
        return super(AccountInvoice, self).action_invoice_open()
