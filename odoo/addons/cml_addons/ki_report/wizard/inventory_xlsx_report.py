from odoo import api, fields, models, _
import xlwt
import base64
from io import BytesIO
from datetime import datetime
from dateutil import relativedelta


class StockInventoryWizard(models.TransientModel):
    _name = "stock.inventory.wizard"
    _description = "stock inventory wizard"

    start_date = fields.Date(
        string="Start Date",
        default=datetime.now().strftime('%Y-%m-01'),
        required=True
    )

    end_date = fields.Date(
        string="End Date",
        default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
        required=True
    )

    # product_id = fields.Many2many(
    #     'product.product',
    #     string="Products"
    # )

    category_id = fields.Many2many(
        'product.category',
        string="Category"
    )


    def xlsxreport(self):
        filename = "Inventory Report.xls"
        workbook = xlwt.Workbook(encoding='utf-8')
        sheet1 = workbook.add_sheet("exel", cell_overwrite_ok=True)
        style2_title_value = xlwt.easyxf("font:color black ;align: horiz left", num_format_str='MM/DD/YYYY')
        style5 = xlwt.easyxf("align:horiz center;align:vertical center;font:color black,bold True;")
        style6 = xlwt.easyxf("align:horiz center;font:color black,bold True;")

        sheet1.col(0).width = 7000
        sheet1.col(1).width = 7000
        sheet1.col(2).width = 7000
        sheet1.col(3).width = 7000
        sheet1.col(4).width = 7000
        sheet1.col(5).width = 7000
        sheet1.col(7).width = 7000
        sheet1.col(8).width = 9000

        sheet1.write_merge(2, 5, 1, 4, "Inventory Report", style5)
        sheet1.write(10, 1, "Categorys", style6)
        sheet1.write(10, 2, "Products", style6)
        sheet1.write(10, 3, "Monthly Sold", style6)
        sheet1.write(10, 4, "Min. Reordering Rule", style6)
        sheet1.write(8, 1, "Start Date", style6)
        sheet1.write(8, 2, self.start_date, style2_title_value)
        sheet1.write(8, 3, "End Date", style6)
        sheet1.write(8, 4, self.end_date, style2_title_value)

        dict = {}
        domain = []
        if self.category_id:
            domain.append(('categ_id', 'in', self.category_id.ids))
        products = self.env['product.product'].sudo().search(domain)
        row_index = 10

        self._cr.execute("""
                    SELECT
                        sum(line.product_uom_qty) as product_uom_qty,
                        line.product_id
                    FROM
                        sale_order_line line
                        LEFT JOIN sale_order AS so ON (line.order_id = so.id)
                    WHERE
                        line.product_id in %s AND
                        so.date_order::date >= %s AND
                        so.date_order::date <= %s AND
                        so.state in  ('sale', 'done')
                    GROUP BY
                        line.product_id""", (tuple(products.ids), self.start_date, self.end_date))

        products_res = self._cr.dictfetchall()

        product_dict = {}
        for rec in products_res:
            product_dict[rec['product_id']] = rec['product_uom_qty']


        for rec in products:
            if rec.categ_id not in dict:
                dict[rec.categ_id] = []
            dict[rec.categ_id].append(rec)
        for record in dict:
            row_index += 1
            sheet1.write(row_index, 1, record.name)

            product_name = dict[record]
            for product in product_name:
                if product_dict.get(product.id, 0) != 0 or product.reordering_min_qty != 0.0:
                    sheet1.write(row_index, 2, product.name)
                    sheet1.write(row_index, 3, product_dict.get(product.id, 0))
                    sheet1.write(row_index, 4, product.reordering_min_qty)
                    row_index += 1


        stream = BytesIO()
        workbook.save(stream)
        out = base64.encodebytes(stream.getvalue())

        exel_id = self.env['stock.inventory.exel'].create({'file_name': filename,
                                                           'excel_file': out
                                                           })


        return {
            'view_mode': 'form',
            'res_id': exel_id.id,
            'res_model': 'stock.inventory.exel',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


class SizeExcelReport(models.TransientModel):
    _name = "stock.inventory.exel"

    file_name = fields.Char(
        'Excel File',
        size=64,
        readonly=True,
    )

    excel_file = fields.Binary(
        'Download Report',
        readonly=True,
    )
