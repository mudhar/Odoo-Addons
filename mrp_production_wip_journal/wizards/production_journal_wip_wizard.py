from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_round
from odoo.exceptions import UserError


class ProductionJournalLine(models.TransientModel):
    _name = 'production_journal.wip_wizard_line'
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', string="Product", required=True, domain="[('id', '=', product_id)]")
    quantity = fields.Float("Quantity", digits=dp.get_precision('Product Unit of Measure'), required=True)
    uom_id = fields.Many2one('product.uom', string='Unit of Measure', related='move_id.product_uom')
    amount_wip_differ = fields.Float(string="Adjust WIP Differ")
    wizard_id = fields.Many2one(comodel_name="production_journal.wip_wizard", string="Wizard")
    move_id = fields.Many2one(comodel_name="stock.move", string="Move")


class ProductionJournal(models.TransientModel):
    _name = 'production_journal.wip_wizard'
    _description = 'Adjust WIP Material'

    production_id = fields.Many2one(comodel_name="mrp.production", string="Manufacturing Order", required=True)
    amount_wip_differ = fields.Float(string="Total WIP Differ",)
    account_expense_material_id = fields.Many2one(comodel_name="account.account",
                                                  string="Expense Account WIP Material Differ")

    product_wip_ids = fields.One2many(comodel_name="production_journal.wip_wizard_line", inverse_name="wizard_id",
                                      string="WIP Material Products")
    partner_id = fields.Many2one(comodel_name="res.partner", string="Vendor CMT", required=True)

    @api.model
    def default_get(self, fields_list):
        res = super(ProductionJournal, self).default_get(fields_list)
        if 'production_id' in fields_list and not res.get('production_id') and self._context.get(
                'active_model') == 'mrp.production' and self._context.get('active_id'):
            res['production_id'] = self._context['active_id']

        if 'amount_wip_differ' in fields_list and not res.get('amount_wip_differ') and res.get('production_id'):
            res['amount_wip_differ'] = self.env['mrp.production'].browse(res['production_id']).amount_wip_differ

        if 'account_expense_material_id' in fields_list and not res.get('account_expense_material_id') and res.get('production_id'):
            res['account_expense_material_id'] = self.env['mrp.production'].browse(
                res['production_id']).account_expense_material_id.id
            if res.get('account_expense_material_id', False):
                self.env['mrp.production'].browse(res['production_id']).set_account_valuation_wip()

        production_id = self.env['mrp.production'].browse(self.env.context.get('active_id'))
        product_moves = []
        if production_id:
            move_consumed = production_id.move_raw_ids.filtered(lambda x: x.state == 'done' and not x.returned_picking)
            move_returned = production_id.move_raw_ids.filtered(lambda x: x.state == 'done' and x.returned_picking)
            for move_consu in move_consumed:
                if move_consu.product_id not in move_returned.mapped('product_id'):
                    quantity = float_round(move_consu.product_qty, precision_rounding=move_consu.product_uom.rounding)
                    product_moves.append((0, 0, {
                        'move_id': move_consu.id,
                        'product_id': move_consu.product_id.id,
                        'uom_id': move_consu.product_id.uom_id.id,
                        'amount_wip_differ': move_consu.value,
                        'quantity': quantity,
                    }))
        if not product_moves:
            raise UserError(_("Tidak Ada Produk Material Yang Sudah Di Return"))
        if 'product_wip_ids' in fields_list:
            res.update({'product_wip_ids': product_moves})
        return res

    @api.multi
    def action_confirm(self):
        account_move_object = self.en['account.move'].sudo()
        for wizard in self:
            debit_account_id = wizard.account_expense_material_id.id
            credit_account_id = wizard.production_id.account_valuation_material_id.id
            account_data = wizard.production_id.product_template_id.get_product_accounts()
            if not account_data.get('stock_journal', False):
                raise UserError(_(
                    'You don\'t have any stock journal defined on your product category,\n '
                    'check if you have installed a chart of accounts \n'))
            ref = ''.join('WIP Material Differ Of %s' % wizard.production_id.display_name)
            if wizard.product_wip_ids and wizard.partner_id:
                for product_wip in wizard.product_wip_ids:
                    if product_wip.product_id:
                        move_lines = wizard.production_id.prepare_account_move_line(product_wip.product_id,
                                                                                    debit_account_id,
                                                                                    credit_account_id,
                                                                                    wizard.partner_id,
                                                                                    ref,
                                                                                    order_ids=wizard.product_wip_ids,
                                                                                    wip='wip_material')
                        date = fields.Date.context_today(self)
                        new_account_move = account_move_object.create({
                            'journal_id': account_data['stock_journal'].id,
                            'line_ids': move_lines,
                            'date': date,
                            'stock_move_id': product_wip.move_id.id,
                            'material_production_id': wizard.production_id.id
                        })
                        new_account_move.post()

        return {'type': 'ir.actions.act_window_close'}