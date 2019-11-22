from openerp import models, fields, api, exceptions, _


class ChangeProductionQty(models.TransientModel):
    _inherit = 'change.production.qty'

    @api.multi
    def change_prod_qty(self):
        """
        Ketika User Melakukan Perubahan Jumlah Quantity Yang Diproduksi.
        Tabel PPIC Line Tidak Melakukan Perubahan Quantity Yang Dibutuhkan Untuk Jumlah Baru Quantity Yang Diproduksi
        :return:
        """
        active_id = self._context.get('active_id')
        assert active_id, _('Active Id not found')
        for production in self.env['mrp.production'].browse(active_id):
            production.write({'product_qty': self.product_qty})
            production.action_compute()

            factor = production.product_uom._compute_qty(production.product_uom.id, production.product_qty,
                                                         production.bom_id.product_uom.id)
            bom_lines, workcenter_details = production.bom_id._ppic_bom_explode(production.product_id, factor / production.product_qty)

            if production.ppic_lines:
                for ppic in production.ppic_lines:
                    for bom_line in bom_lines:
                        if ppic.product_id.id != bom_line['product_id']:
                            continue

                        if ppic.product_id.id == bom_line['product_id']:
                            ppic.write({'product_qty': bom_line.get('product_qty', 0.0) * (production.product_qty / production.bom_id.product_qty)})

            if production.move_lines:
                for move in production.move_lines:
                    for bom_line in bom_lines:
                        if bom_line['product_id'] != move.product_id.id:
                            continue

                        if bom_line['product_id'] == move.product_id.id:
                            move.write({'product_uom_qty': bom_line['product_qty']})

            if production.move_prod_id:
                production.move_prod_id.write({'product_uom_qty': self.product_qty})

            # Update Product To Produce
            for move_line in production.move_created_ids:
                move_line.write({'product_uom_qty': self.product_qty})

        return {'type': 'ir.actions.act_window_close'}











