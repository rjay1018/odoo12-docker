# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Employee Attendance Using Camera",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "version": "12.0.2",
    "license": "OPL-1",
    "summary": """
Attendance By Barcode Module, Attendance By QRCode App,
Attendance Management, Attendance By Mobile Barcode,
Attendance From Mobile Barcode, Attendance Mobile Barcode Scanner,
Attendance Mobile QRCode Scanner Odoo
""",
    "description": """
Do you want to scan Barcode/QRCode in mobile
while Check In & Check Out? Do you want to send notes or
messages when Check In & Check Out?
This is a very unique module which will enhance odoo features
with this module You can manage Check In & Check Out with Barcode/QRCode.
When User Check In & Check Out in Odoo they can write Message,
Comment, or any notes.
So be very quick in all procedures and cheers! Attendance
Mobile Barcode/QRCode Scanner Odoo, Attendance By Barcode Module,
Attendance By QRCode, Attendance Management By Mobile Barcode,
Attendance From Mobile Barcode Scanner Odoo,
Attendance By Barcode Module, Attendance By QRCode App,
Attendance Management, Attendance By Mobile Barcode,
Attendance From Mobile Barcode, Attendance Mobile Barcode Scanner,
Attendance Mobile QRCode Scanner Odoo
""",
    "category": "Employees",
    "depends": [
        "hr_attendance",
    ],
    "data": [
        "views/assets_backend.xml",
    ],
    'qweb': [
        "static/src/xml/attendance.xml",
    ],
    "images": ["static/description/background.png", ],
    "installable": True,
    "application": True,
    "autoinstall": False,
    "price": 140,
    "currency": "EUR"
}
