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
                                                  string="Expense Account WIP Material Differ")
    # account_valuation_service_id = fields.Many2one(comodel_name="account.account",
    #                                                default=lambda self:
    #                                                self.env.user.company_id.account_valuation_service_id,
    #                                                string="Stock Account Valuation WIP Service")

    account_move_ids = fields.One2many(comodel_name="account.move", inverse_name="material_production_id",
                                       string="Reference WIP Material")
    has_balanced = fields.Boolean(string="Has Balanced?")
    has_returned_move = fields.Boolean(compute="_has_returned_moves")
    amount_wip_consumed = fields.Float(string='Total WIP Consumed', digits=dp.get_precision('Account'),
                                       compute="_compute_wip_consumed")
    amount_wip_assembly = fields.Float(string="Total WIP Assembly", digits=dp.get_precision('Account'),
                                       compute="_compute_wip_material_assembly")
    amount_wip_differ = fields.Float(string="Total WIP Materials Differ", digits=dp.get_precision('Account'),
                                     compute="_compute_wip_material_differ",
                                     help="Total Amount Consumed Minus Amount Returned Minus Amount Assembly")
    wip_balance = fields.Boolean(string="WIP Materials Balance", compute="_compute_wip_balance",
                                 index=True)
    account_move_count = fields.Integer(string='Of Account Move', compute="_compute_account_move_count")

    def _compute_account_move_count(self):
        read_group_res = self.env['account.move'].read_group(
            [('material_production_id', 'in', self.ids)], ['material_production_id'], ['material_production_id'])
        mapped_data = dict([(data['material_production_id'][0],
                             data['material_production_id_count']) for data in read_group_res])
        for record in self:
            record.account_move_count = mapped_data.get(record.id, 0)

    @api.multi
    def _compute_wip_balance(self):
        for production in self:
            production.wip_balance = float_is_zero(production.amount_wip_differ,
                                                   precision_digits=production.company_id.currency_id.decimal_places)

    @api.multi
    @api.depends('assembly_plan_id',
                 'move_raw_ids')
    def _compute_wip_material_assembly(self):
        for production in self:
            plan_ids = production.mapped('assembly_plan_id')
            product_moves = production.move_raw_ids.filtered(
                lambda x: not x.returned_picking).mapped('product_id')
            amount_total = production.get_amount_assembly(plan_ids, product_moves)
            if amount_total:
                production.amount_wip_assembly = amount_total

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
                production.amount_wip_consumed = sum(amount_move_consumed)

    @api.multi
    @api.depends('amount_wip_consumed',
                 'amount_wip_assembly',)
    def _compute_wip_material_differ(self):
        for production in self:
            move_returned = production.move_raw_ids.filtered(lambda x: x.returned_picking and x.state == 'done')
            amount_move_returned = 0.0
            if move_returned:
                amount_move_returned += sum(move_returned.mapped('account_move_ids').mapped('amount'))
            amount_differ = production.amount_wip_consumed - amount_move_returned
            if amount_differ and amount_differ > production.amount_wip_assembly:
                amount_wip_differ = amount_differ - production.amount_wip_assembly
                if production.account_move_ids:
                    amount_wip_differ -= sum(production.account_move_ids.mapped('amount'))
                production.amount_wip_differ = amount_wip_differ

            if amount_differ and amount_differ < production.amount_wip_assembly:
                amount_wip_differ = production.amount_wip_assembly - amount_differ
                if production.account_move_ids:
                    amount_wip_differ -= sum(production.account_move_ids.mapped('amount'))
                production.amount_wip_differ = amount_wip_differ

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
        account_valuation_service_id = company.browse(self.company_id.id).mapped('account_valuation_service_id')
        account_expense_material_id = company.browse(self.company_id.id).mapped('account_expense_material_id')
        if not account_valuation_service_id and account_expense_material_id:
            raise UserError(_("Account Valuation WIP Material Dan Jasa Not Found"))

        self.update({
            'account_valuation_service_id': account_valuation_service_id.id,
            'account_expense_material_id': account_expense_material_id.id})

    @api.multi
    def get_amount_assembly(self, plan_ids, product_moves):
        amount_material = []
        amount_accessories = []
        for raw in plan_ids.raw_actual_line_ids.filtered(lambda x: x.product_id.id in product_moves.ids):
            amount_material.append(raw.price_subtotal_actual)
        for cmt in plan_ids.cmt_material_actual_line_ids.filtered(lambda x: x.product_id.id in product_moves.ids):
            amount_accessories.append(cmt.price_subtotal_actual)
        return sum(amount_material) + sum(amount_accessories)

    @api.multi
    def prepare_account_move_line(self, product_id=None, debit_account_id=None, credit_account_id=None,
                                  partner_id=None, ref=False, order_ids=None, wip=None):
        wip_res = []
        for order_id in self:
            if wip == 'wip_service' and order_ids and product_id:
                for plan in order_ids.filtered(lambda x: x.product_id.id == product_id.id):
                    debit_value = order_id.company_id.currency_id.round(plan.price_subtotal)
                    credit_value = debit_value
                    debit_line_vals = {
                        'name': ''.join('%s:%s' % (order_id.name, product_id.name)),
                        'product_id': product_id.id,
                        'quantity': plan.quantity_actual,
                        'product_uom_id': plan.product_uom_id.id,
                        'ref': ref,
                        'partner_id': partner_id.id,
                        'debit': debit_value if debit_value > 0 else 0,
                        'credit': -debit_value if debit_value < 0 else 0,
                        # WIP Jasa
                        'account_id': debit_account_id,
                    }
                    wip_res.append((0, 0, debit_line_vals))
                    credit_line_vals = {
                        'name': ''.join('%s:%s' % (order_id.name, product_id.name)),
                        'product_id': product_id.id,
                        'quantity': plan.quantity_actual,
                        'product_uom_id': plan.product_uom_id.id,
                        'ref': ref,
                        'partner_id': partner_id.id,
                        'credit': credit_value if credit_value > 0 else 0,
                        'debit': -credit_value if credit_value < 0 else 0,
                        # Expense Biaya Produksi
                        'account_id': credit_account_id,
                    }
                    wip_res.append((0, 0, credit_line_vals))

            if wip == 'wip_material' and order_ids:
                for wiz in order_ids:
                    debit_value = order_id.company_id.currency_id.round(wiz.amount_total)
                    credit_value = debit_value
                    debit_line_vals = {
                        'name': ref,
                        'ref': ref,
                        'debit': debit_value if debit_value > 0 else 0,
                        'credit': -debit_value if debit_value < 0 else 0,
                        # WIP Jasa
                        'account_id': debit_account_id,
                    }
                    wip_res.append((0, 0, debit_line_vals))
                    credit_line_vals = {
                        'name': ref,
                        'ref': ref,
                        'credit': credit_value if credit_value > 0 else 0,
                        'debit': -credit_value if credit_value < 0 else 0,
                        # Expense Biaya Produksi
                        'account_id': credit_account_id,
                    }
                    wip_res.append((0, 0, credit_line_vals))

        return wip_res

    @api.multi
    def button_adjust_wip(self):
        self.ensure_one()
        return {
            'name': _('Adjust WIP Differ'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'production_journal.wip_wizard',
            'view_id': self.env.ref('mrp_production_wip_journal.production_journal_wip_wizard_view_form').id,
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'target': 'new',
        }

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


