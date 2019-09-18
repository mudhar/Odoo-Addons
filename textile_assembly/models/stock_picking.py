from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp


class StockPicking(models.Model):
    _inherit = 'stock.picking'


    production_id = fields.Many2one(comodel_name="mrp.production", string="Production Order Finished Product", copy=True)
    raw_material_production_id = fields.Many2one(comodel_name="mrp.production",
                                                 string="Production Order Raw Material", copy=True)

    # Hanya Untuk Informasi Ketika User MRP Membatalkan MO Sedangkan Produk Sudah Terkonsumsi
    # Maka User Diharus Mengembalikan Produk Tsb Dari Lokasi Virtual Production ke Lokasi Stock
    created_return_picking = fields.Boolean(string="Created Return Picking")
    show_button_return = fields.Boolean(string="Display Button Return", compute="_compute_button_return")

    @api.multi
    @api.depends('raw_material_production_id')
    def _compute_button_return(self):
        for picking in self:
            if picking.raw_material_production_id and picking.raw_material_production_id.workorder_ids:
                picking.show_button_return = False
            if picking.raw_material_production_id and not picking.raw_material_production_id.workorder_ids:
                picking.show_button_return = True

    @api.multi
    def action_confirm(self):
        result = super(StockPicking, self).action_confirm()
        for order in self:
            if order.production_id:
                if len(order.production_id.workorder_ids) == 0:
                    raise UserError(_("Belum Ada Proses Work Order Yang Berjalan"))

        return result

    def button_scrap(self):
        res = super(StockPicking, self).button_scrap()
        if self.raw_material_production_id and not self.production_id:
            res['context']['default_production_id'] = self.raw_material_production_id.id

        if self.production_id and not self.raw_material_production_id:
            res['context']['default_production_id'] = self.production_id.id

        return res

    @api.multi
    def button_validate(self):
        result = super(StockPicking, self).button_validate()
        for order in self:
            if order.production_id:
                if len(order.production_id.workorder_ids) == 0:
                    raise UserError(_("Belum Ada Proses Work Order Yang Berjalan"))
            if order.production_id and order.backorder_id:
                count_qc_done = len(order.move_lines.filtered(lambda x: x.is_qc_done))
                if count_qc_done < 1:
                    raise UserError(_("Ada Proses Inputan Belum Selesai"))

        return result


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _create_returns(self):
        result = super(ReturnPicking, self)._create_returns()
        if self.picking_id.raw_material_production_id:
            self.picking_id.write({'created_return_picking': True})
        return result

    def _prepare_move_default_values(self, return_line, new_picking):
        vals = super(ReturnPicking, self)._prepare_move_default_values(return_line, new_picking)
        if self.picking_id.raw_material_production_id:
            vals.update({'returned_picking': True})
        return vals















