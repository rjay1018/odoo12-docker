# Required Sales Agent & Commission Type on New Customers — Design Spec

**Date:** 2026-11-25
**Module:** `sale_commission_extended` (`odoo/addons/cml_addons/sale_commission_extended`)
**Source Requirement:** Request #5 from [Commission & Sales Reports: What We Are Building](https://docs.google.com/document/d/1ooBg6uFWL46gNeQeVufYT1GfxdCCb7b2WTuMvO6QteI/edit?tab=t.0)

## 1. Purpose

When any user creates a new customer in Odoo 12, both **Sales Agent** and **Commission Type** must be filled in before the customer can be saved. This ensures no future invoice is missed during commission runs.

- Applies to all internal users, including support staff creating customers for sales (no exceptions).
- Scoped to **new top-level customers** only (`customer=True`, `agent=False`, `parent_id=False`), so creating vendors, sales agents, internal users, child contacts/addresses, or editing existing legacy customers is not broken.

## 2. Architecture & Approach

**Chosen Approach:** Approach A — enforce in `res.partner.create()` + open up the **Sales Commission** tab and `partner.category.commission` ACL for all internal users.

### 2.1 Model Validation (`models/partner.py`)

Override `create(self, vals_list)` on `res.partner` using `@api.model_create_multi`:

1. Call `partners = super(Partner, self).create(vals_list)` first so Odoo resolves field defaults (`customer`, `agent`, `parent_id`) and materializes `partner_categ_comm_ids` One2many rows in the current transaction.
2. Skip validation when `self.env.context.get('install_mode')` is truthy (module installation/upgrade XML data loading).
3. For each created `partner` in `partners`:
   - Check if `partner.customer and not partner.agent and not partner.parent_id`.
   - If so, verify that `partner.partner_categ_comm_ids` contains at least one line where both `agent_id` and `commission_id` are set.
   - If not, raise `ValidationError`:
     ```python
     _("Sales Agent and Commission Type are required when creating a new customer. "
       "Please add at least one line under the 'Sales Commission' tab.")
     ```
4. Raising `ValidationError` inside `create()` automatically rolls back the database transaction so no incomplete customer record is persisted.
5. `write()` is intentionally not overridden, so existing legacy customers without commission lines can continue to be updated.

### 2.2 View Access (`views/partner.xml`)

- In `view_partner_form_agent` (which adds the **Sales Commission** tab containing `partner_categ_comm_ids`), remove:
  ```xml
  <field name="groups_id" eval="[(4, ref('sales_team.group_sale_salesman'))]"/>
  ```
- This makes the **Sales Commission** tab visible to all internal users (including support staff) when creating or viewing non-agent partners.
- Keep `partner_form_agent_inherit` (Agent Information tab) unchanged.

### 2.3 Security / ACL (`security/ir.model.access.csv`)

- Keep existing `access_partner_category_commission_mngr` (`sales_team.group_sale_manager`, full CRUD: `1,1,1,1`).
- Add `access_partner_category_commission_user` for `base.group_user` on `model_partner_category_commission` with `perm_read=1, perm_write=1, perm_create=1, perm_unlink=0`.
  - Allows any internal user (including support staff) to add and edit Sales Agent + Commission Type lines when creating customers without hitting an AccessError, while keeping line deletion restricted to Sales Managers.

## 3. Data Flow & Edge Cases

| Case | `customer` | `agent` | `parent_id` | Enforced? |
| --- | --- | --- | --- | --- |
| New top-level Customer | `True` | `False` | `False` | **Yes** — requires ≥1 `partner_categ_comm_ids` line with `agent_id` & `commission_id` |
| New Vendor / Supplier | `False` | `False` | `False` | No |
| New Sales Agent | `False` / `True` | `True` | `False` | No |
| New Child Contact / Address | `True` | `False` | Set | No |
| New Odoo User (`res.users`) | `False` | `False` | `False` | No |
| Edit existing legacy Customer | `True` | `False` | `False` | No (`write()` not overridden) |
| Module install / upgrade (`install_mode`) | Any | Any | Any | No |

## 4. Testing & Verification

1. **Automated unit tests** (pure Python / unittest with mocked Odoo environment or Odoo `TransactionCase` in `sale_commission_extended/tests/test_partner_commission_required.py`) covering:
   - Creating a new customer without `partner_categ_comm_ids` raises `ValidationError`.
   - Creating a new customer with a valid `partner_categ_comm_ids` line (`agent_id` + `commission_id`) succeeds.
   - Creating a vendor (`customer=False, supplier=True`), an agent (`agent=True`), a child contact (`parent_id` set), or creating in `install_mode` succeeds without commission lines.
   - Writing to an existing customer without commission lines succeeds.
2. **XML & CSV validation:**
   - Parse `views/partner.xml` with `xml.etree.ElementTree` and confirm `groups_id` is removed from `view_partner_form_agent`.
   - Validate `security/ir.model.access.csv` column structure and group references.
3. **Manual check in Odoo UI** after upgrading `sale_commission_extended`:
   - Test creating a customer as a non-Sales support user (without `group_sale_salesman`) to confirm the **Sales Commission** tab is visible, writable, and enforces the requirement.
