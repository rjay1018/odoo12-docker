# -*- coding: utf-8 -*-

from odoo import models,fields,api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    middlename = fields.Char(
        string="Middle Name",
        copy=False
    )

    @api.depends("firstname", "lastname", "middlename")
    def _compute_name(self):
        return  super(ResPartner, self)._compute_name()

    @api.model
    def _get_computed_name(self, lastname, firstname):
        """Compute the 'name' field according to splitted data.
        You can override this method to change the order of lastname and
        firstname the computed name"""
        name_formula = self._get_names_order()

        print(name_formula)
        record = self
        if name_formula == 'fml':
            name_list = []
            if record.firstname:
                name_list.append(record.firstname)
            if record.middlename:
                middle = record.middlename[0].upper() + '.'
                name_list.append(middle)
            if record.lastname:
                name_list.append(record.lastname)
            if name_list:
                name = ' '.join(name_list)
                return name
        elif name_formula == 'lfm':
            name_list = []
            if record.lastname:
                name_list.append(record.lastname)
            if record.firstname:
                name_list.append(record.firstname)
            if record.middlename:
                middle = record.middlename[0].upper() + '.'
                name_list.append(middle)
            if name_list:
                name = ' '.join(name_list)
                return name
        elif name_formula == 'flm':
            name_list = []
            if record.firstname:
                name_list.append(record.firstname)
            if record.lastname:
                name_list.append(record.lastname)
            if record.middlename:
                name_list.append(record.middlename)
            if name_list:
                name = ' '.join(name_list)
                return name
        else:
            return super(ResPartner, self)._get_computed_name(lastname, firstname)
#         if order == 'last_first_comma':
#             return ", ".join((p for p in (lastname, firstname) if p))
#         elif order == 'first_last':
#             return " ".join((p for p in (firstname, lastname) if p))
#         else:
#             return " ".join((p for p in (lastname, firstname) if p))



    @api.multi
    def _inverse_name_after_cleaning_whitespace(self):
        return True
