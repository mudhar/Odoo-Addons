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
    account_valuation_material_id = fields.Many2one(comodel_name="account.account",
                                                    default=lambda self:
                                                    self.env.user.company_id.account_valuation_material_id,
                                                    string="Stock Account Valuation WIP Material")
    account_valuation_service_id = fields.Many2one(comodel_name="account.account",
                                                   default=lambda self:
                                                   self.env.user.company_id.account_valuation_service_id,
                                                   string="Stock Account Valuation WIP Service")

    account_move_ids = fields.One2many(comodel_name="account.move", inverse_name="material_production_id",
                                       string="Reference WIP Material")
    amount_wip_differ = fields.Float(string="Total WIP Differ", compute="_compute_wip_material_differ")
    is_wip_differ = fields.Boolean(string="Check Amount WIP Differ", compute="_compute_is_wip_differ")
    has_finished_move = fields.Boolean(compute="_has_finished_moves")
    has_returned_move = fields.Boolean(compute="_has_returned_moves")

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

    @api.depends('amount_wip_differ')
    def _compute_is_wip_differ(self):
        for production in self:
            production.is_wip_differ = production.amount_wip_differ

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
            if move_consumed:
                production.amount_wip_differ = production.get_wip_material_amount(move_consumed, move_returned)

    @api.multi
    def set_account_valuation_wip(self):
        company = self.env['res.company']
        account_valuation_material_id = company.browse(self.company_id.id).mapped('account_valuation_material_id')
        account_valuation_service_id = company.browse(self.company_id.id).mapped('account_valuation_service_id')
        account_expense_material_id = company.browse(self.company_id.id).mapped('account_expense_material_id')
        if not account_valuation_service_id and account_valuation_material_id and account_expense_material_id:
            raise UserError(_("Account Valuation WIP Material Dan Jasa Not Found"))

        self.update({'account_valuation_material_id': account_valuation_material_id.id,
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
            amount_move = sum(move_consumed.mapped('account_move_ids').filtered(
                lambda x: x.state == 'posted').mapped('amount')) - \
                sum(move_returned.mapped('account_move_ids').filtered(
                 lambda x: x.state == 'posted').mapped('amount'))
            if amount_move:
                if amount_move > total_plan:
                    amount_balance += (amount_move - total_plan)
            return amount_balance

    def prepare_account_move_line(self, product_id, debit_account_id, credit_account_id,
                                  partner_id, ref, order_ids=None, wip=None):
        wip_res = []
        for order_id in self:
            if wip == 'wip_service' and order_ids:
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
                for wiz in order_ids.filtered(lambda x: x.product_id.id == product_id.id):
                    debit_value = order_id.company_id.currency_id.round(wiz.amount_wip_differ)
                    credit_value = debit_value
                    debit_line_vals = {
                        'name': ''.join('%s:%s' % (order_id.name, product_id.name)),
                        'product_id': product_id.id,
                        'quantity': wiz.quantity,
                        'product_uom_id': wiz.uom_id.id,
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
                        'quantity':wiz.quantity,
                        'product_uom_id': wiz.uom_id.id,
                        'ref': ref,
                        'partner_id': partner_id.id,
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
        # if not self.has_returned_move:
        #     raise UserError(_("Anda Tidak Dapat Melakukan Adjust WIP\n"
        #                       "Karena Anda Belum Selesai Melakukan Return Untuk Material Yang Lebih"))
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

