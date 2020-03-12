# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.tools import float_is_zero, float_compare
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    account_expense_material_id = fields.Many2one(comodel_name="account.account",
                                                  default=lambda self:
                                                  self.env.user.company_id.account_expense_material_id,
                                                  string="Expense Account WIP Differ")

    account_move_ids = fields.One2many(comodel_name="account.move", inverse_name="material_production_id",
                                       string="Reference WIP Material")
    has_balanced = fields.Boolean(string="Has Balanced?")
    has_returned_move = fields.Boolean(compute="_has_returned_moves")
    amount_wip_consumed = fields.Float(string='Total WIP Consumed', digits=dp.get_precision('Account'),
                                       compute="_compute_wip_consumed")
    amount_wip_returned = fields.Float(string='Total WIP Returned', digits=dp.get_precision('Account'),
                                       compute="_compute_wip_returned")
    amount_wip_assembly = fields.Float(string="Total WIP Assembly", digits=dp.get_precision('Account'),
                                       compute="_compute_wip_material_assembly")
    amount_wip_differ = fields.Float(string="Total WIP Differ", digits=dp.get_precision('Account'),
                                     compute="_compute_wip_material_differ",
                                     help="Total Amount Consumed Minus Amount Returned Minus Amount Assembly")
    wip_balance = fields.Boolean(string="WIP Materials Balance", compute="_compute_wip_balance",
                                 index=True)
    account_move_count = fields.Integer(string='Of Account Move', compute="_compute_account_move_count")
    journal_date = fields.Datetime(string='Journal Date')
    produce_done = fields.Boolean(string='Produce done', compute="_check_produce_done")

    def _compute_account_move_count(self):
        read_group_res = self.env['account.move'].read_group(
            [('material_production_id', 'in', self.ids)], ['material_production_id'], ['material_production_id'])
        mapped_data = dict([(data['material_production_id'][0],
                             data['material_production_id_count']) for data in read_group_res])
        for record in self:
            record.account_move_count = mapped_data.get(record.id, 0)

    @api.multi
    @api.depends('move_finished_ids')
    def _check_produce_done(self):
        for production in self:
            production.produce_done = all(move.state == 'done'
                                          for move in production.move_finished_ids) \
                if production.move_finished_ids else False

    @api.multi
    def _compute_wip_balance(self):
        for production in self:
            production.wip_balance = float_is_zero(production.amount_wip_differ,
                                                   precision_digits=production.company_id.currency_id.decimal_places)

    @api.multi
    @api.depends('assembly_plan_id')
    def _compute_wip_material_assembly(self):
        for production in self:
            if production.assembly_plan_id:
                production.amount_wip_assembly = production.assembly_plan_id.amount_total

    @api.multi
    @api.depends('move_raw_ids',
                 'move_raw_ids.state',
                 'move_raw_ids.account_move_ids',
                 'move_raw_ids.account_move_ids.amount')
    def _compute_wip_consumed(self):
        for production in self:
            move_consumed = production.move_raw_ids.filtered(lambda x: not x.returned_picking and x.state == 'done')
            if move_consumed:
                amount_move_consumed = move_consumed.mapped('account_move_ids').filtered(
                    lambda x: x.state == 'posted').mapped('amount')
                amount_service_invoiced = production.get_amount_service_invoiced()
                production.amount_wip_consumed = sum(amount_move_consumed) + sum(amount_service_invoiced)

    @api.multi
    @api.depends('move_raw_ids',
                 'move_raw_ids.state',
                 'move_raw_ids.account_move_ids',
                 'move_raw_ids.account_move_ids.amount')
    def _compute_wip_returned(self):
        for production in self:
            move_returned = production.move_raw_ids.filtered(lambda x: x.returned_picking and x.state == 'done')
            if move_returned:
                amount_move_returned = move_returned.mapped('account_move_ids').filtered(
                    lambda x: x.state == 'posted').mapped('amount')
                production.amount_wip_returned = sum(amount_move_returned)

    @api.multi
    def get_amount_service_invoiced(self):
        amount_service_invoiced = False
        for production in self:
            wo_po = production.workorder_ids.filtered(lambda x: x.po_ids)
            amount_service_invoiced = wo_po.mapped('po_ids').filtered(
                lambda x: x.state == 'done').mapped('amount_untaxed')
        return amount_service_invoiced

    @api.multi
    def _compute_wip_material_differ(self):
        for production in self:
            amount_wip_differ = (
                    (production.amount_wip_consumed - production.amount_wip_returned) - production.amount_wip_assembly)
            amount_account_move = production.account_move_ids.mapped('amount')
            if float_compare(amount_wip_differ, 0.0,
                             precision_rounding=production.company_id.currency_id.rounding) == -1:
                production.amount_wip_differ = sum(amount_account_move) - amount_wip_differ
            if float_compare(amount_wip_differ, 0.0,
                             precision_rounding=production.company_id.currency_id.rounding) == 1:
                production.amount_wip_differ = amount_wip_differ - sum(amount_account_move)

    @api.multi
    @api.depends('move_raw_ids',
                 'move_raw_ids.state',
                 'move_raw_ids.returned_picking')
    def _has_returned_moves(self):
        for mo in self:
            move_returned = mo.move_raw_ids.filtered(lambda x: x.returned_picking and x.state == 'done')
            mo.has_returned_move = any(move_returned)

    @api.multi
    def set_account_valuation_wip(self):
        company = self.env['res.company']
        account_expense_material_id = company.browse(self.company_id.id).mapped('account_expense_material_id')
        if not account_expense_material_id:
            raise UserError(_("Account Valuation WIP Not Found"))

        self.update({
            'account_expense_material_id': account_expense_material_id.id})

    @api.multi
    def prepare_account_move_line(self, debit_account_id=None, credit_account_id=None):
        wip_res = []
        for order_id in self:
            ref = ''.join('WIP Differ Of %s' % order_id.name)
            debit_value = order_id.company_id.currency_id.round(order_id.amount_wip_differ)
            credit_value = debit_value
            debit_line_values = {
                'name': ref,
                'ref': ref,
                'debit': debit_value if debit_value > 0 else 0,
                'credit': -debit_value if debit_value < 0 else 0,
                # WIP Jasa
                'account_id': debit_account_id,
            }
            wip_res.append((0, 0, debit_line_values))
            credit_line_values = {
                'name': ref,
                'ref': ref,
                'credit': credit_value if credit_value > 0 else 0,
                'debit': -credit_value if credit_value < 0 else 0,
                # Expense Biaya Produksi
                'account_id': credit_account_id,
            }
            wip_res.append((0, 0, credit_line_values))

        return wip_res

    @api.multi
    def button_adjust_wip(self):
        self.ensure_one()
        if self.has_returned_move:
            return self.action_adjust_wip()
        else:
            return {
                'name': _('Adjust WIP Differ Warning'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'journal_wip.message_wizard',
                'view_id': self.env.ref('mrp_production_wip_journal.journal_wip_message_wizard_view_form').id,
                'type': 'ir.actions.act_window',
                'context': self.env.context,
                'target': 'new',
            }

    @api.multi
    def action_adjust_wip(self):
        self.check_wo_po()
        if not self.account_expense_material_id:
            self.set_account_valuation_wip()

        account_move_object = self.env['account.move'].sudo()
        location_production = self.product_template_id.property_stock_production
        account_data = self.product_template_id.get_product_accounts()

        if not account_data.get('stock_journal', False):
            raise UserError(_(
                'You don\'t have any stock journal defined on your product category,\n '
                'check if you have installed a chart of accounts \n'))
        if not self.journal_date:
            raise UserError(_("Tanggal Untuk Posting Journal Belum Diisi"))

        if float_compare(self.amount_wip_differ, 0.0, precision_rounding=self.company_id.currency_id.rounding) == 1:
            credit_account_id = location_production.valuation_in_account_id.id
            debit_account_id = self.account_expense_material_id.id
            move_lines = self.prepare_account_move_line(debit_account_id=debit_account_id,
                                                        credit_account_id=credit_account_id)
            new_account_move = account_move_object.create({
                'journal_id': account_data['stock_journal'].id,
                'line_ids': move_lines,
                'date': self.journal_date,
                'material_production_id': self.id,
            })
            new_account_move.post()
            self.write({'has_balance': True})
        if float_compare(self.amount_wip_differ, 0.0, precision_rounding=self.company_id.currency_id.rounding) == -1:
            credit_account_id = self.account_expense_material_id.id
            debit_account_id = location_production.valuation_in_account_id.id
            move_lines = self.prepare_account_move_line(debit_account_id=debit_account_id,
                                                        credit_account_id=credit_account_id)
            new_account_move = account_move_object.create({
                'journal_id': account_data['stock_journal'].id,
                'line_ids': move_lines,
                'date': self.journal_date,
                'material_production_id': self.id,
            })
            new_account_move.post()
            self.write({'has_balance': True})
        return True

    @api.multi
    def action_cancel(self):
        if any(account_move.state == 'posted' for account_move in self.mapped('account_move_ids')):
            raise UserError(_("You can not cancel production order, an account move is posted\n"))

        return super(MrpProduction, self).action_cancel()

    @api.multi
    def action_get_account_moves(self):
        self.ensure_one()
        action_ref = self.env.ref('account.action_move_journal_line')
        if not action_ref:
            return False
        action_data = action_ref.read()[0]
        action_data['domain'] = [('id', 'in', self.account_move_ids.ids)]
        return action_data

    @api.multi
    def action_mark_done(self):
        self.ensure_one()
        if self.amount_wip_differ == 0.0:
            return super(MrpProduction, self).action_mark_done()
        else:
            raise UserError(_("Masih Ada Selisih WIP Material Yang Perlu Di Adjust"))


