# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import float_compare
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    account_expense_material_id = fields.Many2one(comodel_name="account.account",
                                                  default=lambda self:
                                                  self.env.user.company_id.account_expense_material_id,
                                                  string="Expense Account WIP Material Differ")
    account_valuation_service_id = fields.Many2one(comodel_name="account.account",
                                                   default=lambda self:
                                                   self.env.user.company_id.account_valuation_service_id,
                                                   string="Stock Account Valuation WIP Service")

    account_move_ids = fields.One2many(comodel_name="account.move", inverse_name="material_production_id",
                                       string="Reference WIP Material")
    amount_wip_differ = fields.Float(string="Total WIP Materials Differ", compute="_compute_wip_material_differ",
                                     help="Total Amount Consumed Minus Amount Returned Minus Amount Assembly")
    amount_wip_differ_context = fields.Float(string="Total WIP Materials Differ", compute="_compute_wip_material_final")
    amount_wip_assembly = fields.Float(string="Total WIP Assembly", compute="_compute_wip_material_assembly")
    is_wip_differ = fields.Boolean(string="Check Amount WIP Differ", compute="_compute_is_wip_differ", store=True)
    has_finished_move = fields.Boolean(compute="_has_finished_moves")
    has_returned_move = fields.Boolean(compute="_has_returned_moves")

    @api.multi
    @api.depends('amount_wip_differ',
                 'account_move_ids',
                 'account_move_ids.amount',
                 'has_returned_move')
    def _compute_wip_material_final(self):
        for production in self:
          
            if production.has_returned_move and production.account_move_ids:
                production.amount_wip_differ_context = (sum(production.account_move_ids.mapped('amount')) - production.amount_wip_differ)
            if production.has_returned_move and not production.account_move_ids:
                production.amount_wip_differ_context = production.amount_wip_differ

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
                 'move_raw_ids.returned_picking')
    def _has_returned_moves(self):
        for mo in self:
            move_returned = mo.move_raw_ids.filtered(lambda x: x.returned_picking and x.state == 'done')
            mo.has_returned_move = any(move_returned)

    @api.multi
    @api.depends('move_finished_ids')
    def _has_finished_moves(self):
        for mo in self:
            mo.has_finished_move = any(mo.move_finished_ids)

    @api.depends('amount_wip_differ_context')
    def _compute_is_wip_differ(self):
        for production in self:
            production.is_wip_differ = sum(production.amount_wip_differ_context) > 0.0

    @api.depends('has_finished_move',
                 'move_raw_ids',
                 'move_raw_ids.state',
                 'move_raw_ids.account_move_ids',
                 'move_raw_ids.account_move_ids.amount')
    def _compute_wip_material_differ(self):
        for production in self.filtered(
                lambda order_id: order_id.state not in ['done', 'cancel'] and order_id.has_finished_move):
            move_consumed = production.move_raw_ids.filtered(lambda x: x.state == 'done' and not x.returned_picking)
            move_returned = production.move_raw_ids.filtered(lambda x: x.state == 'done' and x.returned_picking)
            amount_total = 0.0
            if move_consumed:
                amount_total += production.get_wip_material_amount(move_consumed, move_returned)
            production.amount_wip_differ = amount_total

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
    def get_wip_material_amount(self, move_consumed, move_returned):
        for production in self:
            amount_balance = 0.0
            product_moves = move_consumed.mapped('product_id')
            plan_id = production.mapped('assembly_plan_id')
            raw_amount = plan_id.raw_actual_line_ids.filtered(
                lambda x: x.product_id.id in product_moves.ids).mapped('price_subtotal_actual')
            cmt_amount = plan_id.cmt_material_actual_line_ids.filtered(
                lambda x: x.product_id.id in product_moves.ids).mapped('price_subtotal_actual')
            total_plan = sum(raw_amount) + sum(cmt_amount)

            total_amount = 0.0
            amount_consumed = production.get_amount_consume(move_consumed.mapped('account_move_ids'))
            amount_returned = production.get_amount_consume(move_returned.mapped('account_move_ids'))
            if amount_consumed and amount_returned or not amount_returned:
                total_amount += sum(amount_consumed) - sum(amount_returned)
            if total_amount > total_plan:
                amount_balance += (total_amount - total_plan)

            return amount_balance

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
    def get_amount_consume(self, account_move_ids):
        amount = []
        for move in account_move_ids.filtered(lambda x: x.state == 'posted'):
            amount.append(move.amount)
        return amount

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
        if not self.has_returned_move:
            return {
                'name': _('Warning Message'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'journal_wip.message_wizard',
                'view_id': self.env.ref('mrp_production_wip_journal.journal_wip_message_wizard_view_form').id,
                'type': 'ir.actions.act_window',
                'context': self.env.context,
                'target': 'new',
            }
        else:
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
    def action_get_account_moves(self):
        self.ensure_one()
        action_ref = self.env.ref('account.action_move_journal_line')
        if not action_ref:
            return False
        action_data = action_ref.read()[0]
        action_data['domain'] = [('id', 'in', self.account_move_ids.ids)]
        return action_data

