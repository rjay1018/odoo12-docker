# Commission Reports by Customer & by Invoice — Design Spec

**Date:** 2026-11-26
**Module:** `sale_commission_extended` (`odoo/addons/cml_addons/sale_commission_extended`)
**Source Requirements:** Requests #1 & #2 from [Commission & Sales Reports: What We Are Building](https://docs.google.com/document/d/1ooBg6uFWL46gNeQeVufYT1GfxdCCb7b2WTuMvO6QteI/edit?tab=t.0)

## 1. Purpose

Add two settlement-based commission reports to `sale_commission_extended`, available as both **QWeb PDF** (Print menu) and **Excel (`.xls`)** downloads directly from `sale.commission.settlement` (no extra wizard/filter needed, since each settlement is already scoped by Sales Agent and Date From / Date To):

1. **Commission Report by Customer** — groups each agent's settled commission lines by customer, showing invoice number, invoice date, product, quantity, unit price, line total, commission rate, and commission amount, with customer subtotals and a grand total.
2. **Commission Report by Invoice** — groups settled commission lines invoice by invoice for auditing, showing customer, invoice date, and sales agent per invoice, followed by product lines (product, quantity, unit price, total, commission rate, commission amount), with invoice subtotals and a grand total.

Returns (credit notes, `invoice.type == 'out_refund'`) are subtracted automatically from quantity, line total, and commission amount.

## 2. Architecture

### 2.1 Shared Report Data Helper (`reports/commission_report_data.py`)

Pure-Python helper functions (usable directly by QWeb report AbstractModels, HTTP Excel controllers, and standalone unit tests without duplicating any math):

- `_resolve_invoice_line(line)`: returns `line.invoice_line`, falling back to `line.agent_line[:1].object_id` or `line.agent_line_categ[:1].object_id`.
- `_format_commission_rate(commission, subtotal=0.0)`:
  - `commission_type == 'pct'`: `'%g%%' % commission.fix_qty` (e.g., `1.5%`)
  - `commission_type == 'fix'`: `'Fixed ({:,.2f})'.format(commission.fix_qty)`
  - `commission_type == 'section'`: finds matching section (`s.amount_from <= abs(subtotal) <= s.amount_to`) and returns `'%g%%' % s.percent`, falling back to `commission.name`.
  - No commission: `''`.
- `_extract_settlement_rows(settlement)`:
  - Iterates `list(settlement.lines) + list(settlement.categ_lines)` (if `categ_lines` exists).
  - For each line, resolves `inv_line`, `invoice = line.invoice or (inv_line.invoice_id if inv_line else False)`, `partner = invoice.partner_id`, `product = inv_line.product_id`, `commission = line.commission`.
  - `is_refund = bool(invoice and getattr(invoice, 'type', '') and 'refund' in invoice.type)`
  - `sign = -1.0 if is_refund else 1.0`
  - `quantity = sign * (inv_line.quantity if inv_line else 0.0)`
  - `price_unit = inv_line.price_unit if inv_line else 0.0`
  - `price_subtotal = sign * (inv_line.price_subtotal if inv_line else 0.0)`
  - `commission_amount = line.settled_amount` (if `is_refund and commission_amount > 0`: negate as safety guard).
  - Deduplicates `price_subtotal` per `inv_line.id` so if multiple commission lines apply to the same invoice line, sales subtotal is counted once while all commission amounts sum.
- `get_by_customer_data(settlement)`:
  - Returns `{'customers': [...], 'grand_total_sales': float, 'grand_total_commission': float}`.
  - Each customer dict: `{'partner': str, 'lines': [...], 'total_sales': float, 'total_commission': float}`.
  - Sorted by customer name (case-insensitive), lines sorted by `(invoice_date, invoice_number, product)`.
- `get_by_invoice_data(settlement)`:
  - Returns `{'invoices': [...], 'grand_total_sales': float, 'grand_total_commission': float}`.
  - Each invoice dict: `{'invoice': str, 'invoice_date': str, 'partner': str, 'agent': str, 'lines': [...], 'total_sales': float, 'total_commission': float}`.
  - Sorted by `(invoice_date, invoice_number)`, lines sorted by `product`.

### 2.2 QWeb PDF Reports

- `reports/commission_by_customer_report.py` (`report.sale_commission_extended.report_commission_by_customer`) + `reports/commission_by_customer_template.xml` (`action_report_commission_by_customer`, string `"Commission Report by Customer"`).
- `reports/commission_by_invoice_report.py` (`report.sale_commission_extended.report_commission_by_invoice`) + `reports/commission_by_invoice_template.xml` (`action_report_commission_by_invoice`, string `"Commission Report by Invoice"`).
- Both bound to `model="sale.commission.settlement"`, registered in `reports/__init__.py` and `__manifest__.py`.

### 2.3 Excel Exports (`controllers/main.py`, `models/settlement.py`, `views/settlement.xml`)

- Add two `xlwt` builder methods + HTTP routes on `CommissionSettlementExport` in `controllers/main.py`:
  - `/sale_commission_extended/export_by_customer/<int:settlement_id>` → `Commission_By_Customer_<Agent>.xls`
  - `/sale_commission_extended/export_by_invoice/<int:settlement_id>` → `Commission_By_Invoice_<Agent>.xls`
- Add `action_export_excel_by_customer` and `action_export_excel_by_invoice` on `sale.commission.settlement` (`models/settlement.py`).
- Add `<button name="action_export_excel_by_customer" string="Export By Customer" .../>` and `<button name="action_export_excel_by_invoice" string="Export By Invoice" .../>` to `<header>` in `views/settlement.xml`.

## 3. Testing & Verification

- Pure-Python `unittest` suite (`tests/test_commission_reports.py`) exercising:
  - `get_by_customer_data`: multi-customer grouping, sorting, subtotals, grand totals, `out_refund` credit note subtraction, multi-commission-line deduplication.
  - `get_by_invoice_data`: multi-invoice grouping, header metadata (customer, date, agent), product lines, subtotals, grand totals, `out_refund` subtraction.
  - `_format_commission_rate`: `pct`, `fix`, `section` (matched & fallback), and `None`.
  - Excel workbook builders (`_build_by_customer_xls`, `_build_by_invoice_xls`) verified via `xlwt` (or clean byte output check).
- `python -m py_compile` on all new/modified `.py` files and `xml.etree.ElementTree` parse check on all new/modified `.xml` files.
