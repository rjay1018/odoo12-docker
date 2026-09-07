from odoo import api, fields, models, _
import xlwt
import base64
from io import BytesIO
from datetime import datetime, date
from dateutil import relativedelta



class FleetVehicleLogFuel(models.Model):
    _inherit = 'fleet.vehicle.log.fuel'

    odometer_start = fields.Float(string="Odometer Start")
    used_km = fields.Float(string="Used KM")
    total_km_liter = fields.Float(string="Total KM/Liter", compute="compute_total_km_liter")

    def compute_total_km_liter(self):
        for rac in self:
            if rac.liter != 0:
                rac.total_km_liter = rac.used_km / rac.liter

    @api.onchange('vehicle_id')
    def _onchange_vehicle(self):
        self.model = self.env['fleet.vehicle.log.fuel'].sudo().search([('vehicle_id', '=', self.vehicle_id.id)],
                                                                      order='date desc, id desc', limit=1)
        if self.vehicle_id:
            self.odometer_unit = self.vehicle_id.odometer_unit
            self.purchaser_id = self.vehicle_id.driver_id.id
            if self.model:
                self.odometer_start = int(self.model.odometer)

    @api.onchange('odometer', 'odometer_start')
    def _onchange_odometer(self):
        self.used_km = self.odometer - self.odometer_start



class FleetFuelReport(models.TransientModel):
    _name = "fleet.fuel.report.wizard"
    _description = "Fuel Report wizard"

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

    fleet_ids = fields.Many2many(
        'fleet.vehicle',
        string="Vehicle"
    )


    def xlsx_fuel_report(self):
        filename = "Fuel Report.xls"
        workbook = xlwt.Workbook(encoding='utf-8')
        sheet1 = workbook.add_sheet("exel", cell_overwrite_ok=True)
        style2_title_value = xlwt.easyxf("font:color black ;align: horiz left", num_format_str='MM/DD/YYYY')
        style5 = xlwt.easyxf("align:horiz center;align:vertical center;font:color black,bold True;")
        style6 = xlwt.easyxf("align:horiz center;font:color black,bold True;")
        style7 = xlwt.easyxf('align:horiz center;')
        style8 = xlwt.easyxf("align:horiz center;", num_format_str='MM/DD/YYYY')

        sheet1.col(0).width = 7000
        sheet1.col(1).width = 7000
        sheet1.col(2).width = 7000
        sheet1.col(3).width = 7000
        sheet1.col(4).width = 7000
        sheet1.col(5).width = 7000
        sheet1.col(7).width = 7000
        sheet1.col(8).width = 9000

        sheet1.write_merge(2, 5, 2, 5, "Fuel Report", style5)
        sheet1.write(8, 2, "Start Date", style6)
        sheet1.write(8, 3, self.start_date, style2_title_value)
        sheet1.write(8, 4, "End Date", style6)
        sheet1.write(8, 5, self.end_date, style2_title_value)


        sheet1.write(10, 0, "Date", style6)
        sheet1.write(10, 1, "Invoice Reference", style6)
        sheet1.write(10, 2, "Odometer Start", style6)
        sheet1.write(10, 3, "Odometer End", style6)
        sheet1.write(10, 4, "Used KM", style6)
        sheet1.write(10, 5, "Total Liter", style6)
        sheet1.write(10, 6, "Total KM/Liter", style6)
        sheet1.write(10, 7, "Total Price", style6)


        if not self.fleet_ids:

            odometer = self.env['fleet.vehicle.log.fuel'].sudo().search([('date', '>=', self.start_date),
                                                                         ('date', '<=', self.end_date)])
            row_index = 11
            list = []
            for rec in odometer:
                row_index += 1
                if rec not in list:
                    list.append(rec)
                    sheet1.write(row_index, 0, rec.date, style8)
                    sheet1.write(row_index, 1, rec.inv_ref or "", style7)
                    sheet1.write(row_index, 2, rec.odometer_start, style7)
                    sheet1.write(row_index, 3, rec.odometer, style7)
                    sheet1.write(row_index, 4, rec.used_km, style7)
                    sheet1.write(row_index, 5, rec.liter, style7)
                    sheet1.write(row_index, 6, rec.total_km_liter, style7)
                    sheet1.write(row_index, 7, rec.amount, style7)


        odometer = self.env['fleet.vehicle.log.fuel'].sudo().search([('vehicle_id', 'in', self.fleet_ids.ids),
                                                                     ('date', '>=', self.start_date),
                                                                     ('date', '<=', self.end_date)])
        row_index = 11
        list = []
        for rec in odometer:
            row_index += 1
            if rec not in list:
                list.append(rec)
                sheet1.write(row_index, 0, rec.date, style8)
                sheet1.write(row_index, 1, rec.inv_ref or "", style7)
                sheet1.write(row_index, 2, rec.odometer_start, style7)
                sheet1.write(row_index, 3, rec.odometer, style7)
                sheet1.write(row_index, 4, rec.used_km, style7)
                sheet1.write(row_index, 5, rec.liter, style7)
                sheet1.write(row_index, 6, rec.total_km_liter, style7)
                sheet1.write(row_index, 7, rec.amount, style7)



        stream = BytesIO()
        workbook.save(stream)
        out = base64.encodebytes(stream.getvalue())

        exel_id = self.env['fuel.report.exel'].create({'file_name': filename,
                                                           'excel_file': out
                                                           })

        return {
            'view_mode': 'form',
            'res_id': exel_id.id,
            'res_model': 'fuel.report.exel',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


class SizeExcelReport(models.TransientModel):
    _name = "fuel.report.exel"

    file_name = fields.Char(
        'Excel File',
        size=64,
        readonly=True,
    )

    excel_file = fields.Binary(
        'Download Report',
        readonly=True,
    )
