from odoo import fields, models, api, _
from odoo.tools.safe_eval import safe_eval
from odoo.osv import expression
from odoo.exceptions import ValidationError
from lxml import etree, html
import time
import logging
import ast

_logger = logging.getLogger(__name__)

FONT_NAMES = [
    ('Calibri','Calibri'),
    ('Times New Roman','Times New Roman'),
    ('Arial','Arial'),
    ('Helvetica','Helvetica'),
    ('Georgia','Georgia'),
]

class MsGenericExcelReport(models.Model):
    _name = "ms.generic.excel.report"
    _description = "Generic Excel Report"

    def _DEFAULT_QUERY(self):
        return """
            SELECT
                column_name
            FROM
                table_name
            WHERE
                {DYNAMIC_WHERE}
        """

    name = fields.Char(string='Report Name', required=True)
    code = fields.Char(string='Code', copy=False, required=True)
    state = fields.Selection([
        ('non_active','Non Active'),
        ('active','Active'),
    ], string='State', default='non_active', copy=False)
    query = fields.Text(string='Text', required=True, default=_DEFAULT_QUERY)
    report_line = fields.One2many('ms.generic.excel.report.line', 'report_id', string='Columns')
    report_filter = fields.One2many('ms.generic.excel.report.filter', 'report_id', string='Filters')
    font_name = fields.Selection(FONT_NAMES, string='Font Name', default='Calibri')
    background_color = fields.Char(string='Header Bg Color', default='#A3E4D7', help='Color code for header background. e.g #A3E4D7')
    parent_menu_id = fields.Many2one('ir.ui.menu', string='Parent Menu', required=False)
    up_menu_id = fields.Many2one('ir.ui.menu', string='Show Below')
    menu_id = fields.Many2one('ir.ui.menu', string='Menu', copy=False)
    groups_id = fields.Many2many(
        comodel_name='res.groups',
        string='Group Name')

    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Report name exist, please check again.'),
        ('unique_code', 'unique(code)', 'Report code exist, please check again.'),
    ]

    def finalize_query(self, query):
        return query

    def static_header(self):
        return []

    def _split_ignoring_parentheses(self, text, delimiter):
        result = []
        current = []
        depth = 0
        for char in text:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            
            if char == delimiter and depth == 0:
                result.append("".join(current))
                current = []
            else:
                current.append(char)
        result.append("".join(current))
        return result

    def get_header_from_query(self):
        headers = []
        final_query = self.get_final_query()
        
        # Lowercase for parsing logic, but keep original for execution if needed (though headers are usually uppercase)
        # Actually, get_header_from_query returns headers which are usually column names.
        # We can work with a lowercased version for parsing.
        final_query_lower = final_query.lower()
        
        # Robustly find the main FROM clause
        select_part = ""
        depth = 0
        i = 0
        
        # We need to look for "from" surrounded by whitespace boundaries
        # Since we are iterating char by char to track depth, we can check for "from" when we hit 'f'
        
        while i < len(final_query_lower):
            char = final_query_lower[i]
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            
            # Check for "from" at depth 0
            # It must be preceded by whitespace (or start of string) and followed by whitespace
            if depth == 0 and final_query_lower[i:].startswith("from"):
                # Check boundaries
                # Preceded by whitespace?
                preceded_by_whitespace = (i == 0) or final_query_lower[i-1].isspace()
                # Followed by whitespace?
                followed_by_whitespace = (i + 4 < len(final_query_lower)) and final_query_lower[i+4].isspace()
                
                if preceded_by_whitespace and followed_by_whitespace:
                     select_part = final_query_lower[:i]
                     break
            i += 1
        
        if not select_part:
            select_part = final_query_lower
            
        if select_part.strip().startswith("select "):
            select_part = select_part.strip()[7:]

        select_query = self._split_ignoring_parentheses(select_part, ',')
        
        for header in select_query:
            header = header.strip()
            if " as " in header:
                header = header.split(" as ")[-1]
            else:
                parts = header.split()
                if parts:
                    candidate = parts[-1]
                    if ')' in candidate and not candidate.endswith(')'):
                         pass
                    elif candidate.endswith(')'):
                         candidate = header
                    
                    if '.' in candidate:
                        candidate = candidate.split('.')[-1]
                    
                    header = candidate

            headers.append(header.upper())
        return headers

    def _clean_query(self, html_content):
        if not html_content:
            return ""
        
        # Basic HTML to text conversion preserving newlines
        # 1. Replace <br>, <p>, <div> with newlines
        text = html_content.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
        text = text.replace('<p>', '\n').replace('</p>', '')
        text = text.replace('<div>', '\n').replace('</div>', '')
        
        # 2. Remove other tags (simple regex)
        # Note: We need to be careful not to remove SQL operators like < or > if they are not tags.
        # But in HTML from Odoo, < and > are usually escaped as &lt; and &gt;
        # So removing <...> tags should be safe for tags.
        # However, if the user typed "x < y" in the editor, it might be stored as "x &lt; y" or "x < y" depending on the editor.
        # If it's "x < y", regex <[^>]+> might match if y is followed by >.
        # But standard Odoo HTML field escapes content.
        
        # Let's use a safer approach if possible, or stick to the simple one if we assume valid HTML.
        # For now, let's stick to the simple regex as it's a common way to strip tags.
        import re
        text = re.sub(r'<[^>]+>', '', text)
        
        # 3. Unescape HTML entities
        text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        
        return text

    def get_final_query(self):
        # final_query = self.env["ir.fields.converter"].text_from_html(self.query).lower()
        # Replaced with custom cleaner and removed .lower()
        final_query = self._clean_query(self.query)
        
        if not final_query:
            raise ValidationError(_("Please input query."))
        elif final_query.strip().lower()[:6] != 'select' :
            raise ValidationError(_("Query must be start with SELECT argument."))
        elif '{dynamic_where}' not in final_query.lower() :
            raise ValidationError(_("Please input where query and include '{DYNAMIC_WHERE}' syntax at the end of where query."))
        where_query = " 1=1 "
        wizard_id = self._context.get('wizard_id')
        if wizard_id :
            wizard_data = wizard_id.read()[0]
            for filter_id in self.report_filter :
                if not filter_id.fields_id :
                    continue
                fields_value = wizard_data[filter_id.fields_id.name]
                if not fields_value :
                    continue
                if filter_id.fields_type == 'selection' :
                    where_query += " AND %s in %s "%(filter_id.column_name, str(tuple(fields_value.split(','))).replace(',)',')'))
                elif filter_id.fields_type == 'date' :
                    if filter_id.operator == 'equal' :
                        operator = '='
                    elif filter_id.operator == 'start_date' :
                        operator = '>='
                    if filter_id.operator == 'end_date' :
                        operator = '<='
                    where_query += " AND %s %s '%s' "%(filter_id.column_name, operator, fields_value.strftime('%Y-%m-%d'))
                elif filter_id.fields_type == 'datetime' :
                    if filter_id.operator == 'equal' :
                        operator = '='
                    elif filter_id.operator == 'start_date' :
                        operator = '>='
                    if filter_id.operator == 'end_date' :
                        operator = '<='
                    where_query += " AND %s %s '%s' "%(filter_id.column_name, operator, fields_value.strftime('%Y-%m-%d %H:%M:%S'))
                elif filter_id.fields_type == 'many2one' :
                    where_query += ' AND %s = %s '%(filter_id.column_name, fields_value[0])
                elif filter_id.fields_type == 'many2many' :
                    where_query += ' AND %s in %s '%(filter_id.column_name, (str(tuple(fields_value)).replace(',)',')')))
        
        # Case insensitive replacement for {dynamic_where}
        # We can use regex to replace it
        import re
        final_query = re.sub(r'\{dynamic_where\}', where_query, final_query, flags=re.IGNORECASE)
        
        return final_query

    def get_data(self):
        self.ensure_one()
        final_query = self.get_final_query()
        try :
            final_query = self.finalize_query(final_query)
            self._cr.execute(final_query)
        except Exception as e :
            raise ValidationError(_(e))
        data = self._cr.fetchall()
        if not data :
            raise ValidationError(_("No data found."))
        return data
    
    def action_active(self):
        self.ensure_one()
        headers = self.static_header()
        if not headers :
            headers = self.get_header_from_query()
        for header in headers :
            self.env['ms.generic.excel.report.line'].create({
                'name': header,
                'report_id': self.id,
            })
        view_id = self.env.ref('ms_generic_excel_report.ms_generic_excel_report_wizard_form_view')
        view_name = 'ms.generic.excel.report.wizard.%s'%(self.code.lower())
        additional_fields = []
        for line in self.report_filter :
            fields_id = line.generate_fields()
            if fields_id.ttype == 'many2many' :
                additional_fields.append('<field name="%s" widget="many2many_tags" options="{\'no_open\':True, \'no_create\':True}"/>'%(fields_id.name))
            elif fields_id.ttype == 'many2one' :
                additional_fields.append('<field name="%s" options="{\'no_open\':True, \'no_create\':True}"/>'%(fields_id.name))
            else :
                additional_fields.append('<field name="%s"/>'%(fields_id.name))
        additional_fields = ' '.join(additional_fields)
        if additional_fields :
            self.env['ir.ui.view'].sudo().create({
                'name': view_name,
                'type': 'form',
                'model': 'ms.generic.excel.report.wizard',
                'inherit_id': view_id.id,
                'mode': 'extension',
                'arch': """
                    <xpath expr="//form/group" position="after">
                        <group string="Filter" col="4" attrs="{'invisible': [('code', '!=', '%s')]}">
                            %s
                        </group>
                    </xpath>
                """ % (self.code, additional_fields),
            })
        action_id = self.env['ir.actions.act_window'].sudo().create({
            'name': self.name,
            'res_model': 'ms.generic.excel.report.wizard',
            'target': 'new',
            'view_mode': 'form',
            'view_id': view_id.id,
            'context': "{'report_id':%d}"%(self.id),
        })
        menu_vals = {
            'name': self.name,
            'action': 'ir.actions.act_window,%d' % (action_id.id,),
            'parent_id': self.parent_menu_id.id,
            'groups_id': [(6, 0, self.groups_id.ids)] if self.groups_id else False,
        }
        if self.up_menu_id :
            menu_vals['sequence'] = self.up_menu_id.sequence
        else :
            menu_vals['sequence'] = -1
        menu_id = self.env['ir.ui.menu'].sudo().create(menu_vals)
        self.write({
            'menu_id': menu_id.id,
            'state': 'active'
        })

    def action_non_active(self):
        self.ensure_one()
        self.report_line.unlink()
        self.sudo().menu_id.action.unlink()
        self.sudo().menu_id.unlink()
        view_name = 'ms.generic.excel.report.wizard.%s' % (self.code.lower())
        view_id = self.env['ir.ui.view'].sudo().search([('name', '=', view_name)])
        if view_id :
            view_id.unlink()
        self.sudo().report_filter.mapped('fields_id').unlink()
        self.write({'state': 'non_active'})

    def write(self, vals):
        if vals.get('name'):
            for report in self :
                if report.sudo().menu_id :
                    report.sudo().menu_id.write({'name':vals['name']})
        return super().write(vals)

class MsGenericExcelReportLine(models.Model):
    _name = "ms.generic.excel.report.line"
    _description = "Generic Excel Report Line"

    report_id = fields.Many2one('ms.generic.excel.report', string='Generic Excel Report', ondelete='cascade')
    name = fields.Char(string='Column Name', required=True)
    
class MsGenericExcelReportFilter(models.Model):
    _name = "ms.generic.excel.report.filter"
    _description = 'Filter generic Excel Report'

    @api.model
    def _list_all_models(self):
        self._cr.execute("SELECT model, name FROM ir_model ORDER BY name")
        return self._cr.fetchall()

    report_id = fields.Many2one('ms.generic.excel.report', string='Generic Excel Report', ondelete='cascade')
    column_name = fields.Char(
        string='Column Name',
        required=True)
    name = fields.Char('Fields Label', required=True)
    fields_type = fields.Selection(
        string='Fields Type',
        selection=[
            ('selection','Selection'),
            ('date','Date'),
            ('datetime','Datetime'),
            ('many2one','Many2one'),
            ('many2many','Many2many'),
        ], required=True)
    selection = fields.Char(
        string='Selection',
        required=False)
    model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Relation',
        required=False)
    fields_id = fields.Many2one(
        comodel_name='ir.model.fields',
        string='Fields',
        required=False)
    fields_domain = fields.Char(
        string="Domain",
        help="Domain for many2one and many2many fields"
    )
    operator = fields.Selection(
        string='Operator',
        selection=[
            ('equal','Equal (=)'),
            ('start_date','As Start Date (>=)'),
            ('end_date','As End Date (>=)'),
        ], required=False)

    @api.onchange('fields_type')
    def onchange_fields_type(self):
        # set default
        if self.fields_type == 'selection' :
            self.selection = "[('fields_name','Fields Label')]"
        elif self.fields_type in ('many2one','many2many'):
            self.fields_domain = '[]'

        # set false
        if self.fields_type != 'selection' :
            self.selection = False
        if self.fields_type not in ('many2one','many2many'):
            self.fields_domain = False
            self.model_id = False
        if self.fields_type not in ('date','datetime'):
            self.operator = False

    @api.onchange('model_id')
    def onchange_model(self):
        self.fields_domain = '[]'

    def generate_fields(self):
        self.ensure_one()
        fields_name = 'x_%s_%s_%s'%(self.report_id.code, self.id, self.column_name)
        fields_name = fields_name.replace('.','')
        fields_name = fields_name.lower()
        model_id = self.env.ref('ms_generic_excel_report.model_ms_generic_excel_report_wizard')
        vals = {
            'model_id': model_id.id,
            'name': fields_name,
            'field_description': self.name,
            'ttype': self.fields_type,
            'state': 'manual',
            'modules': 'ms_generic_excel_report',
        }
        if self.fields_type == 'selection' :
            vals.update({
                'selection': self.selection
            })
        elif self.fields_type == 'many2one' :
            vals.update({
                'relation': self.model_id.model,
            })
        elif self.fields_type == 'many2many' :
            vals.update({
                'relation': self.model_id.model,
            })
        if self.fields_domain :
            vals['domain'] = self.fields_domain
        print('\n vals',vals)
        fields_id = self.env['ir.model.fields'].sudo().create(vals)
        self.write({'fields_id':fields_id.id})
        return fields_id

class IrFieldsConverter(models.AbstractModel): #from OCA
    _inherit = 'ir.fields.converter'

    @api.model
    def text_from_html(self, html_content, max_words=None, max_chars=None, ellipsis=u"...", fail=False):
        html_content = html_content.replace('<p>','').replace('</p>',' ')
        try:
            doc = html.fromstring(html_content)
        except (TypeError, etree.XMLSyntaxError, etree.ParserError):
            if fail:
                raise
            else:
                _logger.exception("Failure parsing this HTML:\n%s", html_content)
                return ""

        # Get words
        words = u"".join(doc.xpath("//text()")).split()

        # Truncate words
        suffix = max_words and len(words) > max_words
        if max_words:
            words = words[:max_words]

        # Get text
        text = u" ".join(words)

        # Truncate text
        suffix = suffix or max_chars and len(text) > max_chars
        if max_chars:
            text = text[:max_chars - (len(ellipsis) if suffix else 0)].strip()

        # Append ellipsis if needed
        if suffix:
            text += ellipsis

        return text
