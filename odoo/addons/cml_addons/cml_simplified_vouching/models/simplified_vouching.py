from odoo import api, fields, models

REMARKS = [
    ('Unpaid', 'Unpaid'), ('Paid', 'Paid'), ('Consignment', 'Consignment'),
    ('MISSING', 'MISSING'), ('CANCELLED', 'CANCELLED'), ('DRAFT', 'DRAFT'),
    ('OEM', 'OEM'), ('Event', 'Event'), ('NO SO - CHECK', 'NO SO - CHECK'),
]

# ponytail: Paid/Unpaid is per Sales Order (all its qualifying invoices), not per delivery.
SQL = """
CREATE MATERIALIZED VIEW simplified_vouching AS (
WITH cfg AS (
    SELECT COALESCE((SELECT value::bigint FROM ir_config_parameter
                     WHERE key = 'delivery_monitoring.start_no'), 48402) AS start_no
), pk AS (
    SELECT sp.id, sp.name, sp.state, sp.origin, sp.partner_id, sp.picking_type_id,
           (sp.scheduled_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Manila')::date AS d,
           CASE WHEN sp.name ~ '^WH/OUT/[0-9]+$' THEN substring(sp.name from 8)::bigint END AS num
    FROM stock_picking sp
    WHERE sp.name LIKE 'WH/OUT/%'
), ly AS (
    SELECT max(extract(year FROM d))::int AS y FROM pk
    WHERE d <= (now() AT TIME ZONE 'Asia/Manila')::date
), so_pay AS (
    SELECT sol.order_id, bool_or(ai.state = 'open') AS has_open
    FROM sale_order_line_invoice_rel r
    JOIN account_invoice_line ail ON ail.id = r.invoice_line_id
    JOIN account_invoice ai ON ai.id = ail.invoice_id
    JOIN sale_order_line sol ON sol.id = r.order_line_id
    WHERE ai.state IN ('open', 'paid') AND ai.type = 'out_invoice'
    GROUP BY sol.order_id
), rem AS (
    SELECT pk.*, so.id AS so_id, so.name AS so_name,
        CASE
            WHEN pk.state = 'cancel' THEN 'CANCELLED'
            WHEN pk.state = 'draft' THEN 'DRAFT'
            WHEN EXISTS (SELECT 1 FROM res_partner_res_partner_category_rel r
                         JOIN res_partner_category c ON c.id = r.category_id
                         WHERE c.name ILIKE 'OEM' AND r.partner_id IN (p.id, p.parent_id)) THEN 'OEM'
            WHEN p.name ILIKE 'Marketing Event' OR pp.name ILIKE 'Marketing Event' THEN 'Event'
            WHEN EXISTS (SELECT 1 FROM res_partner_res_partner_category_rel r
                         JOIN res_partner_category c ON c.id = r.category_id
                         WHERE c.name ILIKE 'Supermarket' AND r.partner_id IN (p.id, p.parent_id)) THEN 'Consignment'
            WHEN so.id IS NULL THEN 'NO SO - CHECK'
            WHEN sp2.order_id IS NOT NULL AND NOT sp2.has_open THEN 'Paid'
            ELSE 'Unpaid'
        END AS remarks,
        CASE WHEN pp.id IS NOT NULL THEN pp.name || ', ' || p.name ELSE p.name END AS partner_name
    FROM pk
    LEFT JOIN sale_order so ON so.name = pk.origin
    LEFT JOIN so_pay sp2 ON sp2.order_id = so.id
    LEFT JOIN res_partner p ON p.id = pk.partner_id
    LEFT JOIN res_partner pp ON pp.id = p.parent_id
), mv AS (
    SELECT m.picking_id, m.sale_line_id, (ld.usage = 'customer') AS to_cust,
           SUM(CASE WHEN m.state = 'done' THEN COALESCE(dq.q, 0) ELSE m.product_uom_qty END) AS q
    FROM stock_move m
    JOIN pk ON pk.id = m.picking_id
    JOIN stock_location ld ON ld.id = m.location_dest_id
    LEFT JOIN (SELECT move_id, SUM(qty_done) AS q FROM stock_move_line GROUP BY move_id) dq
           ON dq.move_id = m.id
    WHERE m.state NOT IN ('draft', 'cancel') AND m.sale_line_id IS NOT NULL
    GROUP BY m.picking_id, m.sale_line_id, (ld.usage = 'customer')
), dm AS (
    SELECT picking_id, sale_line_id, q, SUM(q) OVER (PARTITION BY sale_line_id) AS tq
    FROM mv WHERE to_cust
), inv AS (
    SELECT r.order_line_id AS sale_line_id,
           SUM(ail.price_subtotal * CASE WHEN ai.type = 'out_refund' THEN -1 ELSE 1 END) AS val
    FROM sale_order_line_invoice_rel r
    JOIN account_invoice_line ail ON ail.id = r.invoice_line_id
    JOIN account_invoice ai ON ai.id = ail.invoice_id
    WHERE ai.state IN ('draft', 'open', 'paid')
    GROUP BY r.order_line_id
), inv_cons AS (
    SELECT ir.stock_consigments_id AS sc_id, ail.product_id,
           SUM(ail.price_subtotal * CASE WHEN ai.type = 'out_refund' THEN -1 ELSE 1 END) AS val
    FROM account_invoice_stock_consigments_rel ir
    JOIN account_invoice ai ON ai.id = ir.account_invoice_id
    JOIN account_invoice_line ail ON ail.invoice_id = ai.id
    WHERE ai.state IN ('draft', 'open', 'paid')
      AND NOT EXISTS (SELECT 1 FROM sale_order_line_invoice_rel r WHERE r.invoice_line_id = ail.id)
    GROUP BY ir.stock_consigments_id, ail.product_id
), cdm AS (
    SELECT sc_id, product_id, picking_id, sale_line_id, q,
           SUM(q) OVER (PARTITION BY sc_id, product_id) AS tq
    FROM (
        SELECT DISTINCT scl.consignments_id AS sc_id, scl.product_id, dm.picking_id, dm.sale_line_id, dm.q
        FROM stock_consigments_lines scl
        JOIN sale_order_line_stock_consigments_lines_rel r ON r.stock_consigments_lines_id = scl.id
        JOIN dm ON dm.sale_line_id = r.sale_order_line_id
    ) x
), amt AS (
    SELECT picking_id, SUM(alloc) AS amount FROM (
        SELECT dm.picking_id,
               ROUND(inv.val * SUM(dm.q) OVER w / NULLIF(dm.tq, 0), 2)
             - ROUND(inv.val * (SUM(dm.q) OVER w - dm.q) / NULLIF(dm.tq, 0), 2) AS alloc
        FROM dm JOIN inv ON inv.sale_line_id = dm.sale_line_id
        WINDOW w AS (PARTITION BY dm.sale_line_id ORDER BY dm.picking_id)
        UNION ALL
        SELECT cdm.picking_id,
               ROUND(ic.val * SUM(cdm.q) OVER w / NULLIF(cdm.tq, 0), 2)
             - ROUND(ic.val * (SUM(cdm.q) OVER w - cdm.q) / NULLIF(cdm.tq, 0), 2) AS alloc
        FROM cdm JOIN inv_cons ic ON ic.sc_id = cdm.sc_id AND ic.product_id = cdm.product_id
        WINDOW w AS (PARTITION BY ic.sc_id, ic.product_id ORDER BY cdm.picking_id, cdm.sale_line_id)
    ) a GROUP BY picking_id
), amt_so AS (
    SELECT mv.picking_id,
           SUM(mv.q * sol.price_subtotal / NULLIF(sol.product_uom_qty, 0)) AS amount
    FROM mv
    JOIN rem ON rem.id = mv.picking_id
    JOIN sale_order_line sol ON sol.id = mv.sale_line_id
    WHERE mv.to_cust OR rem.remarks = 'Event'
    GROUP BY mv.picking_id
)
SELECT rem.id AS id, rem.d AS scheduled_date, rem.name AS name, rem.partner_id,
       rem.partner_name, rem.so_name, rem.remarks, rem.picking_type_id,
       CASE WHEN rem.remarks IN ('Event', 'Consignment') THEN COALESCE(amt.amount, amt_so.amount)
            WHEN rem.remarks IN ('Paid', 'Unpaid') THEN amt.amount END AS amount,
       (extract(year FROM rem.d)::int = ly.y) AS is_latest_year
FROM rem LEFT JOIN amt ON amt.picking_id = rem.id
         LEFT JOIN amt_so ON amt_so.picking_id = rem.id, ly
UNION ALL
SELECT 1000000000 + g, prev.d, 'WH/OUT/' || g, NULL, NULL, NULL, 'MISSING', NULL, NULL,
       (extract(year FROM prev.d)::int = ly.y)
FROM cfg, ly,
     generate_series(cfg.start_no, (SELECT max(num) FROM pk)) g
LEFT JOIN LATERAL (SELECT d FROM pk WHERE num < g ORDER BY num DESC LIMIT 1) prev ON TRUE
WHERE NOT EXISTS (SELECT 1 FROM pk WHERE pk.num = g)
) WITH DATA
"""


class SimplifiedVouching(models.Model):
    _name = 'simplified.vouching'
    _description = 'Simplified Vouching'
    _auto = False
    _order = 'name desc'

    scheduled_date = fields.Date('Scheduled Date')
    name = fields.Char('WH/OUT')
    partner_id = fields.Many2one('res.partner', 'Customer')
    partner_name = fields.Char('Customer Name')
    so_name = fields.Char('SO (#)')
    remarks = fields.Selection(REMARKS, 'Remarks')
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type')
    amount = fields.Float('AMOUNT')
    is_latest_year = fields.Boolean('Latest Year')

    @api.model_cr
    def init(self):
        cr = self.env.cr
        cr.execute("SELECT relkind FROM pg_class WHERE relname = 'simplified_vouching'")
        row = cr.fetchone()
        if row:
            kind = 'MATERIALIZED VIEW' if row[0] == 'm' else 'VIEW'
            cr.execute('DROP %s simplified_vouching CASCADE' % kind)
        cr.execute(SQL)
        cr.execute('CREATE UNIQUE INDEX simplified_vouching_id_idx ON simplified_vouching (id)')

    @api.model
    def refresh(self):
        # ponytail: snapshot refreshed by cron; data is at most 10 min old
        self.env.cr.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY simplified_vouching')
