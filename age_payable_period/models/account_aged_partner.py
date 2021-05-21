from dateutil.relativedelta import relativedelta
from odoo import fields, models, _
from odoo.tools import float_is_zero
from odoo.tools.misc import format_date
from odoo.tools.profiler import profile


class ReportAccountAgePayable(models.AbstractModel):
    """extend models account.aged.payable"""
    _inherit = "account.aged.payable"

    @profile
    def _get_columns_name(self, options):
        """replace header column name of aged payable report"""
        company = self.env.user.company_id
        columns = [
            {},
            {'name': _("Due Date"), 'class': 'date', 'style': 'white-space:nowrap;'},
            {'name': _("Journal"), 'class': '', 'style': 'text-align:center; white-space:nowrap;'},
            {'name': _("Account"), 'class': '', 'style': 'text-align:center; white-space:nowrap;'},
            {'name': _("Exp. Date"), 'class': 'date', 'style': 'white-space:nowrap;'},
            {'name': _("As of: %s") % format_date(
                self.env, options['date']['date_to']), 'class': 'number sortable',
             'style': 'white-space:nowrap;'},
        ]
        column1 = "%s - %s" % (str(company.column1_from), str(company.column1_to))
        column2 = "%s - %s" % (str(company.column2_from), str(company.column2_to))
        column3 = "%s - %s" % (str(company.column3_from), str(company.column3_to))
        column4 = "%s - %s" % (str(company.column4_from), str(company.column4_to))
        columns.append({'name': _(column1), 'class': 'number sortable',
                        'style': 'white-space:nowrap;'})
        columns.append({'name': _(column2), 'class': 'number sortable',
                        'style': 'white-space:nowrap;'})
        columns.append({'name': _(column3), 'class': 'number sortable',
                        'style': 'white-space:nowrap;'})
        columns.append({'name': _(column4), 'class': 'number sortable',
                        'style': 'white-space:nowrap;'})
        columns.append({'name': _("Older"), 'class': 'number sortable',
                        'style': 'white-space:nowrap;'})
        columns.append({'name': _("Total"), 'class': 'number sortable',
                        'style': 'white-space:nowrap;'})
        return columns


class ReportAgedPartnerBalance(models.AbstractModel):
    """
    Overwritten method list value move line if there is a parameter in settings
    """
    _inherit = 'report.account.report_agedpartnerbalance'
    _description = 'Aged Partner Balance Report'

    def _get_partner_move_lines(self, account_type, date_from, target_move, period_length):
        """extend/replace base function for payable report configuration"""
        ctx = self._context
        if ctx.get('model') != 'account.aged.payable' and not ctx.get('aged_balance'):
            results, total, amls = super(ReportAgedPartnerBalance, self)._get_partner_move_lines(
                account_type, date_from, target_move, period_length)
            return results, total, amls
        # This method can receive the context key 'include_nullified_amount' {Boolean}
        # Do an invoice and a payment and unreconcile. The amount will be nullified
        # By default, the partner wouldn't appear in this report.
        # The context key allow it to appear
        # In case of a period_length of 30 days as of 2019-02-08, we want the following periods:
        # Name       Stop         Start
        # 1 - 30   : 2019-02-07 - 2019-01-09
        # 31 - 60  : 2019-01-08 - 2018-12-10
        # 61 - 90  : 2018-12-09 - 2018-11-10
        # 91 - 120 : 2018-11-09 - 2018-10-11
        # +120     : 2018-10-10
        company = self.env.user.company_id
        periods = {}
        date_from = fields.Date.from_string(date_from)
        start = date_from
        # Part Change Period
        periods['4'] = {
            'name': "%s-%s" % (str(company.column1_from), str(company.column1_to)),
            'stop': (start - relativedelta(days=company.column1_from)).strftime('%Y-%m-%d'),
            'start': (start - relativedelta(days=company.column1_to)).strftime('%Y-%m-%d'),
        }
        periods['3'] = {
            'name': "%s-%s" % (str(company.column2_from), str(company.column2_to)),
            'stop': (start - relativedelta(days=company.column2_from)).strftime('%Y-%m-%d'),
            'start': (start - relativedelta(days=company.column2_to)).strftime('%Y-%m-%d'),
        }
        periods['2'] = {
            'name': "%s-%s" % (str(company.column3_from), str(company.column3_to)),
            'stop': (start - relativedelta(days=company.column3_from)).strftime('%Y-%m-%d'),
            'start': (start - relativedelta(days=company.column3_to)).strftime('%Y-%m-%d'),
        }
        periods['1'] = {
            'name': "%s-%s" % (str(company.column4_from), str(company.column4_to)),
            'stop': (start - relativedelta(days=company.column4_from)).strftime('%Y-%m-%d'),
            'start': (start - relativedelta(days=company.column4_to)).strftime('%Y-%m-%d'),
        }
        periods['0'] = {
            'name': '+ ' + str(company.column4_to),
            'stop': (start - relativedelta(days=company.column4_to + 1)).strftime('%Y-%m-%d'),
            'start': False,
        }
        # End Part change
        res = []
        total = []
        partner_clause = ''
        cr = self.env.cr
        user_company = self.env.company
        user_currency = user_company.currency_id
        company_ids = self._context.get('company_ids') or [user_company.id]
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']
        arg_list = (tuple(move_state), tuple(account_type), date_from,)
        if 'partner_ids' in ctx:
            if ctx['partner_ids']:
                partner_clause = 'AND (l.partner_id IN %s)'
                arg_list += (tuple(ctx['partner_ids'].ids),)
            else:
                partner_clause = 'AND l.partner_id IS NULL'
        if ctx.get('partner_categories'):
            partner_clause += 'AND (l.partner_id IN %s)'
            partner_ids = self.env['res.partner'].search([('category_id', 'in', ctx['partner_categories'].ids)]).ids
            arg_list += (tuple(partner_ids or [0]),)
        arg_list += (date_from, tuple(company_ids))

        query = '''
                    SELECT DISTINCT l.partner_id, res_partner.name AS name, UPPER(res_partner.name) AS UPNAME, CASE WHEN prop.value_text IS NULL THEN 'normal' ELSE prop.value_text END AS trust
                    FROM account_move_line AS l
                      LEFT JOIN res_partner ON l.partner_id = res_partner.id
                      LEFT JOIN ir_property prop ON (prop.res_id = 'res.partner,'||res_partner.id AND prop.name='trust' AND prop.company_id=%s),
                      account_account, account_move am
                    WHERE (l.account_id = account_account.id)
                        AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.internal_type IN %s)
                        AND (
                                l.reconciled IS NOT TRUE
                                OR EXISTS (
                                    SELECT id FROM account_partial_reconcile where max_date > %s
                                    AND (credit_move_id = l.id OR debit_move_id = l.id)
                                )
                            )
                            ''' + partner_clause + '''
                        AND (l.date <= %s)
                        AND l.company_id IN %s
                    ORDER BY UPPER(res_partner.name)
                    '''
        arg_list = (self.env.company.id,) + arg_list
        cr.execute(query, arg_list)

        partners = cr.dictfetchall()
        # put a total of 0
        for i in range(7):
            total.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id'] for partner in partners]
        lines = dict((partner['partner_id'], []) for partner in partners)
        if not partner_ids:
            return [], [], {}

        lines[False] = []
        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        for i in range(5):
            args_list = (tuple(move_state), tuple(account_type), tuple(partner_ids),)
            dates_query = '(COALESCE(l.date_maturity,l.date)'

            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s)'
                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (periods[str(i)]['stop'],)
            args_list += (date_from, tuple(company_ids))

            query = '''SELECT l.id
                            FROM account_move_line AS l, account_account, account_move am
                            WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                                AND (am.state IN %s)
                                AND (account_account.internal_type IN %s)
                                AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                                AND ''' + dates_query + '''
                            AND (l.date <= %s)
                            AND l.company_id IN %s
                            ORDER BY COALESCE(l.date_maturity, l.date)'''
            cr.execute(query, args_list)
            partners_amount = {}
            aml_ids = [x[0] for x in cr.fetchall()]
            # prefetch the fields that will be used; this avoid cache misses,
            # which look up the cache to determine the records to read, and has
            # quadratic complexity when the number of records is large...
            move_lines = self.env['account.move.line'].browse(aml_ids)
            move_lines._read(['partner_id', 'company_id', 'balance', 'matched_debit_ids', 'matched_credit_ids'])
            move_lines.matched_debit_ids._read(['max_date', 'company_id', 'amount'])
            move_lines.matched_credit_ids._read(['max_date', 'company_id', 'amount'])
            for line in move_lines:
                partner_id = line.partner_id.id or False
                if partner_id not in partners_amount:
                    partners_amount[partner_id] = 0.0
                line_amount = line.company_id.currency_id._convert(line.balance, user_currency, user_company, date_from,
                                                                   round=False)
                if user_currency.is_zero(line_amount):
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount += partial_line.company_id.currency_id._convert(partial_line.amount, user_currency,
                                                                                    user_company, date_from,
                                                                                    round=False)
                for partial_line in line.matched_credit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount -= partial_line.company_id.currency_id._convert(partial_line.amount, user_currency,
                                                                                    user_company, date_from,
                                                                                    round=False)

                line_amount = user_currency.round(line_amount)
                if not self.env.company.currency_id.is_zero(line_amount):
                    partners_amount[partner_id] += line_amount
                    lines.setdefault(partner_id, [])
                    lines[partner_id].append({
                        'line': line,
                        'amount': line_amount,
                        'period': i + 1,
                    })
            history.append(partners_amount)

        # This dictionary will store the not due amount of all partners
        undue_amounts = {}
        query = '''SELECT l.id
                        FROM account_move_line AS l, account_account, account_move am
                        WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                            AND (am.state IN %s)
                            AND (account_account.internal_type IN %s)
                            AND (COALESCE(l.date_maturity,l.date) >= %s)\
                            AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                        AND (l.date <= %s)
                        AND l.company_id IN %s
                        ORDER BY COALESCE(l.date_maturity, l.date)'''
        cr.execute(query, (
        tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, tuple(company_ids)))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids):
            partner_id = line.partner_id.id or False
            if partner_id not in undue_amounts:
                undue_amounts[partner_id] = 0.0
            line_amount = line.company_id.currency_id._convert(line.balance, user_currency, user_company, date_from,
                                                               round=False)
            if user_currency.is_zero(line_amount):
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.max_date <= date_from:
                    line_amount += partial_line.company_id.currency_id._convert(partial_line.amount, user_currency,
                                                                                user_company, date_from, round=False)
            for partial_line in line.matched_credit_ids:
                if partial_line.max_date <= date_from:
                    line_amount -= partial_line.company_id.currency_id._convert(partial_line.amount, user_currency,
                                                                                user_company, date_from, round=False)
            line_amount = user_currency.round(line_amount)
            if not self.env.company.currency_id.is_zero(line_amount):
                undue_amounts[partner_id] += line_amount
                lines.setdefault(partner_id, [])
                lines[partner_id].append({
                    'line': line,
                    'amount': line_amount,
                    'period': 6,
                })

        for partner in partners:
            if partner['partner_id'] is None:
                partner['partner_id'] = False
            at_least_one_amount = False
            values = {}
            undue_amt = 0.0
            if partner['partner_id'] in undue_amounts:  # Making sure this partner actually was found by the query
                undue_amt = undue_amounts[partner['partner_id']]

            total[6] = total[6] + undue_amt
            values['direction'] = undue_amt
            if not float_is_zero(values['direction'], precision_rounding=self.env.company.currency_id.rounding):
                at_least_one_amount = True

            for i in range(5):
                during = False
                if partner['partner_id'] in history[i]:
                    during = [history[i][partner['partner_id']]]
                # Adding counter
                total[(i)] = total[(i)] + (during and during[0] or 0)
                values[str(i)] = during and during[0] or 0.0
                if not float_is_zero(values[str(i)], precision_rounding=self.env.company.currency_id.rounding):
                    at_least_one_amount = True
            values['total'] = sum([values['direction']] + [values[str(i)] for i in range(5)])
            # Add for total
            total[(i + 1)] += values['total']
            values['partner_id'] = partner['partner_id']
            if partner['partner_id']:
                name = partner['name'] or ''
                values['name'] = len(name) >= 45 and not self.env.context.get('no_format') and name[
                                                                                               0:41] + '...' or name
                values['trust'] = partner['trust']
            else:
                values['name'] = _('Unknown Partner')
                values['trust'] = False

            if at_least_one_amount or (self._context.get('include_nullified_amount') and lines[partner['partner_id']]):
                res.append(values)
        return res, total, lines
