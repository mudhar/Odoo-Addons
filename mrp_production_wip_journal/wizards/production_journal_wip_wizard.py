from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.tools import float_is_zero
from odoo.exceptions import UserError


class ProductionJournal(models.TransientModel):
    _name = 'production_journal.wip_wizard'
    _description = 'Adjust WIP Material'

    production_id = fields.Many2one(comodel_name="mrp.production", string="Manufacturing Order", required=True)
    amount_wip_differ = fields.Float(string="Total WIP Material Differ")
    amount_total = fields.Float(string="Amount To Adjust", required=True)
    account_expense_material_id = fields.Many2one(comodel_name="account.account",
                                                  string="Expense Account WIP Material Differ")
    currency_id = fields.Many2one('res.currency', 'Currency', readonly=True)

    @api.onchange('amount_total')
    def _onchange_amount_total(self):
        if self.amount_total > self.amount_wip_differ:
            raise UserError(_("Total WIP Yang Di Adjust Tidak Boleh Lebih Besar Dari WIP Material Differ"))

    @api.model
    def default_get(self, fields_list):
        res = super(ProductionJournal, self).default_get(fields_list)
        if 'production_id' in fields_list and not res.get('production_id') and self._context.get(
                'active_model') == 'mrp.production' and self._context.get('active_id'):
            res['production_id'] = self._context['active_id']

        if 'currency_id' in fields_list and not res.get('currency_id') and res.get('production_id'):
            res['currency_id'] = self.env['mrp.production'].browse(res['production_id']).company_id.currency_id.id

        if 'amount_wip_differ' in fields_list and not res.get('amount_wip_differ') and res.get('production_id'):
            res['amount_wip_differ'] = self.env['mrp.production'].browse(res['production_id']).amount_wip_differ_context

        if 'account_expense_material_id' in fields_list and not res.get('account_expense_material_id') and res.get('production_id'):
            res['account_expense_material_id'] = self.env['mrp.production'].browse(
                res['production_id']).account_expense_material_id.id
            if res.get('account_expense_material_id', False):
                self.env['mrp.production'].browse(res['production_id']).set_account_valuation_wip()
        return res

    @api.multi
    def check_balanced(self):
        for wizard in self:
            amount_balanced = 0.0
            production_id = self.env['mrp.production'].browse(wizard.production_id.id)
            if production_id and production_id.amount_wip_differ_context:
                amount_balanced += production_id.amount_wip_differ_context - wizard.amount_total
            if float_is_zero(amount_balanced, precision_digits=wizard.currency_id.decimal_places):
                wizard.production_id.write({'has_balanced': True})
        return True

    @api.multi
    def action_confirm(self):
        account_move_object = self.env['account.move'].sudo()
        for wizard in self:
            wizard.check_balanced()

            location_production = wizard.production_id.product_template_id.property_stock_production
            debit_account_id = wizard.account_expense_material_id.id
            credit_account_id = location_production.valuation_in_account_id.id
            # debit_account_id = location_production.valuation_in_account_id.id
            # credit_account_id = wizard.account_expense_material_id.id
            account_data = wizard.production_id.product_template_id.get_product_accounts()
            if not account_data.get('stock_journal', False):
                raise UserError(_(
                    'You don\'t have any stock journal defined on your product category,\n '
                    'check if you have installed a chart of accounts \n'))
            ref = ''.join('WIP Material Differ Of %s' % wizard.production_id.display_name)
            if wizard.amount_total and wizard.account_expense_material_id:
                move_lines = wizard.production_id.prepare_account_move_line(debit_account_id=debit_account_id,
                                                                            credit_account_id=credit_account_id,
                                                                            wip='wip_material',
                                                                            ref=ref,
                                                                            order_ids=wizard)
                date = fields.Date.context_today(self)
                new_account_move = account_move_object.create({
                    'journal_id': account_data['stock_journal'].id,
                    'line_ids': move_lines,
                    'date': date,
                    'material_production_id': wizard.production_id.id
                })
                new_account_move.post()



        return {'type': 'ir.actions.act_window_close'}