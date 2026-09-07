# -*- coding: utf-8 -*-

from odoo.http import request,route
from odoo.addons.portal.controllers.portal import CustomerPortal, pager


class CustomerPortal(CustomerPortal):


    @route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        if "name" in self.MANDATORY_BILLING_FIELDS:
            self.MANDATORY_BILLING_FIELDS.remove("name")
        if "firstname" not in self.MANDATORY_BILLING_FIELDS:
            self.MANDATORY_BILLING_FIELDS.append("firstname")
        if "lastname" not in self.MANDATORY_BILLING_FIELDS:
            self.MANDATORY_BILLING_FIELDS.append("lastname")
        if "middlename" not in self.MANDATORY_BILLING_FIELDS:
            self.MANDATORY_BILLING_FIELDS.append("middlename")

        call_super = super(CustomerPortal, self).account(redirect,**post)

        return call_super