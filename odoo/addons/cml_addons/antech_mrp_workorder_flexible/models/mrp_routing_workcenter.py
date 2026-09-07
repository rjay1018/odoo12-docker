# -*- coding: utf-8 -*-
from odoo import fields, models


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    worksheet = fields.Binary('PDF', help="Upload your PDF file.")
    worksheet_type = fields.Selection([
        ('pdf', 'PDF'), ('google_slide', 'Google Slide')],
        string="Work Sheet", default="pdf",
        help="Defines if you want to use a PDF or a Google Slide as work sheet."
    )
    worksheet_google_slide = fields.Char('Google Slide',
                                         help="Paste the url of your Google Slide. Make sure the access to the document is public.")
