from odoo import api, fields, models
from dateutil.relativedelta import relativedelta

FETCH_RANGE = 2500

class InsPartnerAgeing(models.TransientModel):
    _inherit = "ins.partner.ageing"

    # Add a new Boolean field for excluding empty rows
    exclude_empty_rows = fields.Boolean(
        string="Exclude Empty Rows",
        default=True,
        help="If checked, partners with all-zero balances will be excluded from the report."
    )
    salesperson_ids = fields.Many2many('res.users', string="Salespersons", required=False)


    @api.multi
    def write(self, vals):
        """
        Fully overrides the write method to handle modifications to partner_ids,
        partner_category_ids, and salesperson_ids before updating the record.
        """

        # Override partner_ids handling
        if 'partner_ids' in vals:
            partner_ids = vals.get('partner_ids', [])
            if partner_ids:
                vals['partner_ids'] = [(6, 0, partner_ids)]
            else:
                vals['partner_ids'] = [(5, 0, 0)]  # Clears the many2many field

        # Override salesperson_ids handling
        if 'salesperson_ids' in vals:
            salesperson_ids = vals.get('salesperson_ids', [])
            if salesperson_ids:
                vals['salesperson_ids'] = [(6, 0, salesperson_ids)]
            else:
                vals['salesperson_ids'] = [(5, 0, 0)]  # Clears the many2many field

        return super().write(vals)

    def get_filters(self, default_filters={}):
        filter_dict = super().get_filters(default_filters)
        salespersons = self.salesperson_ids if self.salesperson_ids else self.env['res.users'].search([])
        filter_dict.update({
            'salesperson_ids': self.salesperson_ids.ids,
            'salesperson_list': [(s.id, s.name) for s in salespersons],
        })
        return filter_dict

    def process_filters(self):
        filters = super().process_filters()
        data = self.get_filters(default_filters={})
        filters.update({
            'salespersons': self.env['res.users'].browse(data.get('salesperson_ids', [])).mapped(
                'name') if data.get('salesperson_ids') else ['All'],
            'salesperson_list': data.get('salesperson_list'),
        })
        return filters

    def prepare_bucket_list(self):
        periods = {}
        date_from = self.as_on_date
        date_from = fields.Date.from_string(date_from)

        lang = self.env.user.lang
        language_id = self.env['res.lang'].search([('code', '=', lang)])[0]

        bucket_list = [self.bucket_1,self.bucket_2,self.bucket_3,self.bucket_4,self.bucket_5]

        start = False
        stop = date_from
        name = 'Not Due'
        periods[0] = {
            'bucket': 'As on',
            'name': name,
            'start': '',
            'stop': stop.strftime('%Y-%m-%d'),
        }

        stop = date_from
        final_date = False
        for i in range(5):
            start = stop - relativedelta(days=1)
            days_to_subtract = bucket_list[i] - (bucket_list[i-1] if i > 0 else 0)
            stop = start - relativedelta(days=days_to_subtract - 1)
            name = '0 - ' + str(bucket_list[0]) if i==0 else  str(str(bucket_list[i-1] + 1)) + ' - ' + str(bucket_list[i])
            final_date = stop
            periods[i+1] = {
                'bucket': bucket_list[i],
                'name': name,
                'start': start.strftime('%Y-%m-%d'),
                'stop': stop.strftime('%Y-%m-%d'),
            }

        start = final_date -relativedelta(days=1)
        stop = ''
        name = str(self.bucket_5) + ' +'

        periods[6] = {
            'bucket': 'Above',
            'name': name,
            'start': start.strftime('%Y-%m-%d'),
            'stop': '',
        }
        return periods

    def process_detailed_data(self, offset=0, partner=0, fetch_range=FETCH_RANGE):
        '''

        It is used for showing detailed move lines as sub lines. It is defered loading compatable
        :param offset: It is nothing but page numbers. Multiply with fetch_range to get final range
        :param partner: Integer - Partner
        :param fetch_range: Global Variable. Can be altered from calling model
        :return: count(int-Total rows without offset), offset(integer), move_lines(list of dict)
        '''
        as_on_date = self.as_on_date
        period_dict = self.prepare_bucket_list()
        period_list = [period_dict[a]['name'] for a in period_dict]
        company_id = self.env.user.company_id

        salesperson_ids = tuple(self.salesperson_ids.ids) if self.salesperson_ids else None

        type = ('receivable', 'payable')
        if self.type:
            type = tuple([self.type, 'none'])

        offset = offset * fetch_range
        count = 0

        if partner:

            sql = """
                    SELECT COUNT(*)
                    FROM
                        account_move_line AS l
                    LEFT JOIN
                        account_move AS m ON m.id = l.move_id
                    LEFT JOIN
                        account_account AS a ON a.id = l.account_id
                    LEFT JOIN
                        account_account_type AS ty ON a.user_type_id = ty.id
                    LEFT JOIN
                        account_journal AS j ON l.journal_id = j.id
                    WHERE
                        l.balance <> 0
                        AND m.state = 'posted'
                        AND ty.type IN %s
                        AND l.partner_id = %s
                        AND l.date <= '%s'
                        AND l.company_id = %s
                        AND LOWER(j.type) NOT IN ('bank', 'cash')
                """ % (type, partner, as_on_date, company_id.id)
            self.env.cr.execute(sql)
            count = self.env.cr.fetchone()[0]

            SELECT = """SELECT m.name AS move_name,
                                m.id AS move_id,
                                l.date AS date,
                                l.date_maturity AS date_maturity,
                                j.name AS journal_name,
                                cc.id AS company_currency_id,
                                rp.name AS sales_person_name,
                                ai.date_invoice as date_invoice,
                                a.name AS account_name, """

            for period in period_dict:
                if period_dict[period].get('start') and period_dict[period].get('stop'):
                    SELECT += """ CASE
                                    WHEN
                                        COALESCE(l.date_maturity,l.date) >= '%s' AND
                                        COALESCE(l.date_maturity,l.date) <= '%s'
                                    THEN
                                        sum(l.balance) +
                                        sum(
                                            COALESCE(
                                                (SELECT
                                                    SUM(amount)
                                                FROM account_partial_reconcile
                                                WHERE credit_move_id = l.id AND max_date <= '%s'), 0
                                                )
                                            ) -
                                        sum(
                                            COALESCE(
                                                (SELECT
                                                    SUM(amount)
                                                FROM account_partial_reconcile
                                                WHERE debit_move_id = l.id AND max_date <= '%s'), 0
                                                )
                                            )
                                    ELSE
                                        0
                                    END AS %s,""" % (period_dict[period].get('stop'),
                                                     period_dict[period].get('start'),
                                                     as_on_date,
                                                     as_on_date,
                                                     'range_' + str(period),
                                                     )
                elif not period_dict[period].get('start'):
                    SELECT += """ CASE
                                    WHEN
                                        COALESCE(l.date_maturity,l.date) >= '%s'
                                    THEN
                                        sum(
                                            l.balance
                                            ) +
                                        sum(
                                            COALESCE(
                                                (SELECT
                                                    SUM(amount)
                                                FROM account_partial_reconcile
                                                WHERE credit_move_id = l.id AND max_date <= '%s'), 0
                                                )
                                            ) -
                                        sum(
                                            COALESCE(
                                                (SELECT
                                                    SUM(amount)
                                                FROM account_partial_reconcile
                                                WHERE debit_move_id = l.id AND max_date <= '%s'), 0
                                                )
                                            )
                                    ELSE
                                        0
                                    END AS %s,""" % (
                    period_dict[period].get('stop'), as_on_date, as_on_date, 'range_' + str(period))
                else:
                    SELECT += """ CASE
                                    WHEN
                                        COALESCE(l.date_maturity,l.date) <= '%s'
                                    THEN
                                        sum(
                                            l.balance
                                            ) +
                                        sum(
                                            COALESCE(
                                                (SELECT
                                                    SUM(amount)
                                                FROM account_partial_reconcile
                                                WHERE credit_move_id = l.id AND max_date <= '%s'), 0
                                                )
                                            ) -
                                        sum(
                                            COALESCE(
                                                (SELECT
                                                    SUM(amount)
                                                FROM account_partial_reconcile
                                                WHERE debit_move_id = l.id AND max_date <= '%s'), 0
                                                )
                                            )
                                    ELSE
                                        0
                                    END AS %s """ % (
                    period_dict[period].get('start'), as_on_date, as_on_date, 'range_' + str(period))

            sql = """
                    FROM
                        account_move_line AS l
                    LEFT JOIN
                        account_move AS m ON m.id = l.move_id
                    LEFT JOIN
                        account_invoice AS ai ON ai.id = l.invoice_id
                    LEFT JOIN
                        res_users AS ru ON ru.id = ai.user_id
                    LEFT JOIN
                        res_partner AS rp ON ru.partner_id = rp.id
                    LEFT JOIN
                        account_account AS a ON a.id = l.account_id
                    LEFT JOIN
                        account_account_type AS ty ON a.user_type_id = ty.id
                    LEFT JOIN
                        account_journal AS j ON l.journal_id = j.id
                    LEFT JOIN
                        res_currency AS cc ON l.company_currency_id = cc.id
                    WHERE
                        l.balance <> 0
                        AND m.state = 'posted'
                        AND ty.type IN %s
                        AND l.partner_id = %s
                        AND l.date <= %s
                        AND l.company_id = %s
                        AND LOWER(j.type) NOT IN ('bank', 'cash')

                """
            if salesperson_ids:
                sql += " AND ru.id IN %s"

            sql += """
                GROUP BY
                    l.date, l.date_maturity, m.id, m.name, j.name, a.name, cc.id, rp.name, ai.date_invoice
                OFFSET %s ROWS
                FETCH FIRST %s ROWS ONLY
            """

            # ✅ Adjust parameters dynamically
            if salesperson_ids:
                params = (type, partner, as_on_date, company_id.id, salesperson_ids, offset, fetch_range)
            else:
                sql = sql.replace(" AND ru.id IN %s", "")
                params = (type, partner, as_on_date, company_id.id, offset, fetch_range)

            self.env.cr.execute(SELECT + sql, params)
            final_list = self.env.cr.dictfetchall() or []
            move_lines = []
            for m in final_list:
                if (m['range_0'] or m['range_1'] or m['range_2'] or m['range_3'] or m['range_4'] or m['range_5'] or m['range_6']):
                    move_lines.append(m)

            if move_lines:
                return count, offset, move_lines, period_list
            else:
                return 0, 0, [], []

    def process_data(self):
        ''' Query Start Here
        ['partner_id':
            {'0-30':0.0,
            '30-60':0.0,
            '60-90':0.0,
            '90-120':0.0,
            '>120':0.0,
            'as_on_date_amount': 0.0,
            'total': 0.0}]
        1. Prepare bucket range list from bucket values
        2. Fetch partner_ids and loop through bucket range for values
        '''
        period_dict = self.prepare_bucket_list()
        company_id = self.env.user.company_id
        domain = ['|', ('company_id', '=', company_id.id), ('company_id', '=', False)]
        if self.partner_type == 'customer':
            domain.append(('customer', '=', True))
        if self.partner_type == 'supplier':
            domain.append(('supplier', '=', True))

        if self.partner_category_ids:
            domain.append(('category_id', 'in', self.partner_category_ids.ids))

        partner_ids = self.partner_ids or self.env['res.partner'].search(domain)

        as_on_date = self.as_on_date
        company_currency_id = company_id.currency_id.id

        type = ('receivable', 'payable')
        if self.type:
            type = tuple([self.type, 'none'])

        if self.salesperson_ids:
            salesperson_ids_list = list(self.salesperson_ids.ids)
            salesperson_ids = tuple(salesperson_ids_list)
        else:
            salesperson_ids = None

        partner_dict = {}
        for partner in partner_ids:
            partner_dict.update({partner.id: {}})

        partner_dict.update({'Total': {}})

        for period in period_dict:
            partner_dict['Total'].update({period_dict[period]['name']: 0.0})

        partner_dict['Total'].update({'total': 0.0, 'partner_name': 'ZZZZZZZZZ'})
        partner_dict['Total'].update({'company_currency_id': company_currency_id})



        for partner in partner_ids:
            partner_dict[partner.id].update({'partner_name': partner.name})

            total_balance = 0.0

            sql = """
                SELECT
                    COUNT(*) AS count
                FROM
                    account_move_line AS l
                LEFT JOIN
                    account_move AS m ON m.id = l.move_id
                LEFT JOIN
                    account_invoice AS ai ON ai.id = l.invoice_id
                LEFT JOIN
                    res_users AS ru ON ru.id = ai.user_id
                LEFT JOIN
                    account_account AS a ON a.id = l.account_id
                LEFT JOIN
                    account_account_type AS ty ON a.user_type_id = ty.id
                WHERE
                    l.balance <> 0
                    AND m.state = 'posted'
                    AND ty.type IN %s
                    AND l.partner_id = %s
                    AND l.date <= %s
                    AND l.company_id = %s

            """

            if salesperson_ids:
                sql += " AND ru.id IN %s"
                params = (type, partner.id, as_on_date, company_id.id, salesperson_ids)
            else:
                sql = sql.replace(" AND ru.id IN %s", "")  # Remove the condition if no salesperson
                params = (type, partner.id, as_on_date, company_id.id,)
            self.env.cr.execute(sql, params)
            fetch_dict = self.env.cr.dictfetchone() or 0.0
            count = fetch_dict.get('count') or 0.0

            if count:
                for period in period_dict:
                    where = " AND l.date <= '%s' AND l.partner_id = %s AND COALESCE(l.date_maturity,l.date) " % (
                    as_on_date, partner.id)
                    if period_dict[period].get('start') and period_dict[period].get('stop'):
                        where += " BETWEEN '%s' AND '%s'" % (
                        period_dict[period].get('stop'), period_dict[period].get('start'))
                    elif not period_dict[period].get('start'):  # ie just
                        where += " >= '%s'" % (period_dict[period].get('stop'))
                    else:
                        where += " <= '%s'" % (period_dict[period].get('start'))
                    sql = """
                        SELECT
                            sum(l.balance) AS balance,
                            sum(COALESCE((SELECT SUM(amount)FROM account_partial_reconcile
                                WHERE credit_move_id = l.id AND max_date <= %s), 0)) AS sum_debit,
                            sum(COALESCE((SELECT SUM(amount) FROM account_partial_reconcile
                                WHERE debit_move_id = l.id AND max_date <= %s), 0)) AS sum_credit
                        FROM
                            account_move_line AS l
                        LEFT JOIN
                            account_move AS m ON m.id = l.move_id
                        LEFT JOIN
                            account_invoice AS ai ON ai.id = l.invoice_id
                        LEFT JOIN
                            res_users AS ru ON ru.id = ai.user_id
                        LEFT JOIN
                            account_account AS a ON a.id = l.account_id
                        LEFT JOIN
                            account_account_type AS ty ON a.user_type_id = ty.id
                        LEFT JOIN
                            account_journal AS j ON l.journal_id = j.id
                        WHERE
                            l.balance <> 0
                            AND m.state = 'posted'
                            AND ty.type IN %s
                            AND l.company_id = %s
                            AND LOWER(j.type) NOT IN ('bank', 'cash')

                    """
                    if salesperson_ids:
                        sql += " AND ru.id IN %s"
                        params = (as_on_date, as_on_date, type, company_id.id, salesperson_ids)
                    else:
                        sql = sql.replace(" AND ru.id IN %s", "")
                        params = (as_on_date, as_on_date, type, company_id.id)
                    amount = 0.0

                    self.env.cr.execute(sql + where, params)
                    fetch_dict = self.env.cr.dictfetchall() or 0.0

                    if not fetch_dict[0].get('balance'):
                        amount = 0.0
                    else:
                        amount = fetch_dict[0]['balance'] + fetch_dict[0]['sum_debit'] - fetch_dict[0]['sum_credit']
                        total_balance += amount

                    partner_dict[partner.id].update({period_dict[period]['name']: amount})
                    partner_dict['Total'][period_dict[period]['name']] += amount
                partner_dict[partner.id].update({'count': count})
                partner_dict[partner.id].update({'pages': self.get_page_list(count)})
                partner_dict[partner.id].update({'single_page': True if count <= FETCH_RANGE else False})
                partner_dict[partner.id].update({'total': total_balance})
                partner_dict['Total']['total'] += total_balance
                partner_dict[partner.id].update({'company_currency_id': company_currency_id})
                partner_dict['Total'].update({'company_currency_id': company_currency_id})

            else:
                partner_dict.pop(partner.id, None)

        if self.exclude_empty_rows:
            filtered_partner_dict = {}
            for partner_id, data in partner_dict.items():
                if partner_id == 'Total':
                    # Always include the 'Total' row
                    filtered_partner_dict[partner_id] = data
                    continue

                # Check if any bucket has a non-zero value
                has_non_zero_balance = any(
                    data.get(period_dict[period]['name'], 0.0) != 0.0 for period in period_dict
                )

                if has_non_zero_balance:
                    filtered_partner_dict[partner_id] = data

            return period_dict, filtered_partner_dict

        return period_dict, partner_dict
