# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MrpWorkOrder(models.Model):
    _inherit = 'mrp.workorder'

    @api.multi
    def button_receive_good(self):
        result = super(MrpWorkOrder, self).button_receive_good()
        for work_order in self:
            if not work_order.production_id.account_valuation_service_id:
                work_order.production_id.set_account_valuation_wip()
            if not work_order.product_service_ids.mapped('account_move_ids'):
                work_order.create_account_move()
        return result

    @api.multi
    def create_account_move(self):
        account_move_object = self.env['account.move'].sudo()
        for order_id in self:
            if not order_id.next_work_order_id and not order_id.is_cutting:
                for service in order_id.product_service_ids:
                    if service.product_id and order_id.partner_id:
                        debit_account_id = order_id.production_id.account_valuation_service_id.id
                        credit_account_id = service.product_id.categ_id.property_account_expense_categ_id.id

                        account_data = service.product_id.product_tmpl_id.get_product_accounts()
                        if not account_data.get('stock_journal', False):
                            raise UserError(_(
                                'You don\'t have any stock journal defined on your product category, check if you have installed a chart of accounts'))

                        ref = service.work_order_id.display_name
                        plan_id = order_id.production_id.mapped('assembly_plan_id')
                        cmt_service_ids = plan_id.cmt_service_ids.filtered(
                            lambda x: x.product_id.id == service.product_id.id)
                        move_lines = order_id.production_id.prepare_account_move_line(product_id=service.product_id,
                                                                                      debit_account_id=debit_account_id,
                                                                                      credit_account_id=credit_account_id,
                                                                                      partner_id=order_id.partner_id,
                                                                                      ref=ref,
                                                                                      order_ids=cmt_service_ids,
                                                                                      wip='wip_service')

                        if not order_id.backdate_finished:
                            raise UserError(_("Harap Isi Tanggal Selesai Proses %s") % order_id.name)

                        new_account_move = account_move_object.create({
                            'journal_id': account_data['stock_journal'].id,
                            'line_ids': move_lines,
                            'date': order_id.backdate_finished,
                            'work_order_service_id': service.id,
                        })
                        new_account_move.post()
        return True




