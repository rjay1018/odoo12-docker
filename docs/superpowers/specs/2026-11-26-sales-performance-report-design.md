# Sales Performance Report vs. Wholesale Price (Miss Tan) — Design Spec

**Date:** 2026-11-26
**Module:** `sale_commission_extended` (`odoo/addons/cml_addons/sale_commission_extended`)
**Source Requirement:** Request #3 from [Commission & Sales Reports: What We Are Building](https://docs.google.com/document/d/1ooBg6uFWL46gNeQeVufYT1GfxdCCb7b2WTuMvO6QteI/edit?tab=t.0)

## 1. Purpose

Replace the manually maintained `SalesReport2026` Excel file with a system-generated monthly/quarterly **Sales Performance Report** per Sales Agent, comparing each product's Average Selling Price (ASP) against the Wholesale Price List and tracking agent product quotas.

## 2. Architecture

### 2.1 Wholesale Price List Flag (`models/product.py`, `views/product.xml`)
- Inherit `product.pricelist` and add `is_wholesale_pricelist = fields.Boolean('Is Wholesale Pricelist', default=False)`.
- Expose `is_wholesale_pricelist` on `product.product_pricelist_view`.

### 2.2 Agent Product Quotas (`models/partner.py`, `views/partner.xml`, `security/ir.model.access.csv`)
- New model `sale.commission.agent.quota`:
  - `agent_id = fields.Many2one('res.partner', 'Sales Agent', required=True, ondelete='cascade')`
  - `product_id = fields.Many2one('product.product', 'Product', required=True)`
  - `quota_qty = fields.Float('Quota Qty', required=True)`
  - Constraint preventing duplicate `(agent_id, product_id)`.
- On `res.partner`: `quota_ids = fields.One2many('sale.commission.agent.quota', 'agent_id', string='Product Quotas')`.
- Add a **Quotas** tab inside `partner_form_agent_inherit` (`Agent Information` notebook in `views/partner.xml`).
- ACL: `sales_team.group_sale_manager` (`1,1,1,1`), `base.group_user` (`1,0,0,0`).

### 2.3 Shared Calculation Engine (`reports/sales_performance_data.py`)
Pure-Python calculation module (no top-level Odoo imports) shared by QWeb PDF, `xlwt` Excel export, and standalone `unittest`:
- `get_period_bounds(period_type, year, quarter=None, month=None)` → `(date_from, date_to, period_label, month_columns)` where `month_columns` is `[(month_int, label), ...]` (3 entries for quarterly, 1 for monthly).
- `compute_sales_performance(agent_name, period_label, month_columns, invoice_line_records, catalog_products, wholesale_prices, quota_map)`:
  - Aggregates by `product_id` (no duplicate product rows), automatically subtracting `out_refund` credit notes from `total_qty`, monthly qty buckets, `subtotal_amount`, and `commission_amount`.
  - Computes per product: `uom`, `total_qty`, `month_qtys`, `subtotal_amount`, `comm_rate_display`, `commission_amount`, `avg_selling_price`, `wholesale_price`, `missing_wholesale_price` flag, `evaluation` (`No Sale` / `Below BM` / `Above BM` / `No Wholesale Price`), `quota`, `realization`, `quota_status` (`Pass` / `Fail` / `N/A`).
  - Builds top summary block: `agent`, `period`, `total_amount`, dynamic `category_totals` (summing exactly to `total_amount`), `commission_total`, `commission_paid`, `commission_unpaid`, `above_bm_count`, `below_bm_count`, `no_sale_count`, `above_bm_rate`, `quota_pass_count`, `quota_fail_count`, `quota_na_count`.

### 2.4 Wizard, PDF & Excel Export
- `wizard/sales_performance_wizard.py` (`sale.commission.sales.performance.wizard`) + `wizard/sales_performance_wizard_view.xml`:
  - Menu under `sale_commission.menu_sale_commissions_management`: **Sales Performance Report**.
  - Fields: `agent_id`, `period_type` (`quarter`/`month`), `year`, `quarter`, `month`, `pricelist_id` (defaulting to `product.pricelist` where `is_wholesale_pricelist=True`).
  - Actions: `action_export_excel()` (downloads `.xls` via `/sale_commission_extended/export_sales_performance/<int:wizard_id>`) and `action_print_pdf()` (QWeb PDF `report_sales_performance`).
- `reports/sales_performance_report.py` + `reports/sales_performance_template.xml`.
- `controllers/main.py`: `/sale_commission_extended/export_sales_performance/<int:wizard_id>` using `xlwt`.
