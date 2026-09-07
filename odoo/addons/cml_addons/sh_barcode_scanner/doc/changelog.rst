12.0.1
=======
- initial release.
12.0.2
-----
code changed.

                    if stock_picking_line.quantity_done == stock_picking_line.product_uom_qty + 1:
                        raise Warning('Becareful! Quantity exceed than initial demand!')  



12.0.3 (Date : 8 May 2019)
-------

- Inventoried Location problem solved in inventory adjustment barcode scan.(Inventoried Location and Location in inventory line must be same)
-
 

--------
12.0.4
-------------
- new standard odoo widget="barcode_handler" implemented.
- new settings given to scan internal reference or barcode or both.

=========

12.0.5 (25 July 2019)
-------------
- in picking, product uom qty is set to 1 rather than 0 when first barcode scanned.
 

12.0.6 (2 September 2019)
-------------
- In lines, Last scanned product move to top, Last scanned product change color and play sound while warning/error features added.

12.0.7 (18 September 2019)
-------------
- Auto close error/alert message popup after some miliseconds.
 

12.0.8 (21 FEB 2020)
-------------
-  Bug Fixed: in Sale, Discount not apply from pricelist when product added by Scanner.
	call line._onchange_discount() method in sale model file.
	
	
==> Multi Barcode REMOVED.


12.0.9 (Date: 11 July 2020)
=========================
==> QR Scanning Support Added.




12.0.10 (Date: 2 Step 2020)
=========================
==> Barcode Scanning support for detailed operation added without lot/serial no.

12.0.11 (19 Feb 2021)
==================
==> [Add] Global Document Search Added.
==> [Add] Scan Barcode and add into barcode field in product variant and template.

12.0.12 (29 Jan 2022)
=====================
==> [update] if product not has multi variant open template view



