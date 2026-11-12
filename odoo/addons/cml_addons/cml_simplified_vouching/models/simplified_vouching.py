from odoo import api, fields, models

REMARKS = [
    ('Unpaid', 'Unpaid'), ('Paid', 'Paid'), ('Consignment', 'Consignment'),
    ('MISSING', 'MISSING'), ('CANCELLED', 'CANCELLED'), ('DRAFT', 'DRAFT'),
    ('OEM', 'OEM'), ('Event', 'Event'), ('NO SO - CHECK', 'NO SO - CHECK'),
]

# ponytail: allocation is not rounded per delivery; add a remainder-to-last-delivery
# step if the client needs cent-exact reconciliation.
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
            WHEN pt.name ILIKE '%marketing event%' THEN 'Event'
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
    LEFT JOIN stock_picking_type pt ON pt.id = pk.picking_type_id
), dm AS (
    SELECT m.picking_id, m.sale_line_id, SUM(ml.qty_done) AS q,
           SUM(SUM(ml.qty_done)) OVER (PARTITION BY m.sale_line_id) AS tq
    FROM stock_move m
    JOIN stock_move_line ml ON ml.move_id = m.id
    JOIN stock_picking_type t ON t.id = m.picking_type_id AND t.code = 'outgoing'
    WHERE m.state = 'done' AND m.sale_line_id IS NOT NULL
    GROUP BY m.picking_id, m.sale_line_id
), inv AS (
    SELECT r.order_line_id AS sale_line_id,
           SUM(ail.price_subtotal * CASE WHEN ai.type = 'out_refund' THEN -1 ELSE 1 END) AS val
    FROM sale_order_line_invoice_rel r
    JOIN account_invoice_line ail ON ail.id = r.invoice_line_id
    JOIN account_invoice ai ON ai.id = ail.invoice_id
    WHERE ai.state IN ('open', 'paid')
    GROUP BY r.order_line_id
), amt AS (
    SELECT dm.picking_id,
           SUM(COALESCE(inv.val, CASE WHEN rem.remarks IN ('Event', 'Consignment')
                                      THEN sol.price_subtotal END)
               * dm.q / NULLIF(dm.tq, 0)) AS amount
    FROM dm
    JOIN rem ON rem.id = dm.picking_id
    JOIN sale_order_line sol ON sol.id = dm.sale_line_id
    LEFT JOIN inv ON inv.sale_line_id = dm.sale_line_id
    GROUP BY dm.picking_id
)
SELECT rem.id AS id, rem.d AS scheduled_date, rem.name AS name, rem.partner_id,
       rem.partner_name, rem.so_name, rem.remarks, rem.picking_type_id,
       CASE WHEN rem.remarks IN ('Paid', 'Unpaid', 'Event', 'Consignment')
            THEN amt.amount END AS amount,
       (extract(year FROM rem.d)::int = ly.y) AS is_latest_year
FROM rem LEFT JOIN amt ON amt.picking_id = rem.id, ly
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
        cr.execute('DROP VIEW IF EXISTS simplified_vouching CASCADE')
        cr.execute('DROP MATERIALIZED VIEW IF EXISTS simplified_vouching CASCADE')
        cr.execute(SQL)
        cr.execute('CREATE UNIQUE INDEX simplified_vouching_id_idx ON simplified_vouching (id)')

    @api.model
    def refresh(self):
        # ponytail: snapshot refreshed by cron; data is at most 10 min old
        self.env.cr.execute('REFRESH MATERIALIZED VIEW CONCURRENTLY simplified_vouching')
