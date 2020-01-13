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
    is_rejected = fields.Boolean(string="Check Picking Reject")

    @api.multi
    def action_confirm(self):
        result = super(StockPicking, self).action_confirm()
        for order in self:
            if order.production_id:
                if len(order.production_id.workorder_ids) == 0:
                    raise UserError(_("Belum Ada Proses Work Order Yang Berjalan"))

        return result

    # def button_scrap(self):
    #     res = super(StockPicking, self).button_scrap()
    #     if self.raw_material_production_id and not self.production_id:
    #         res['context']['default_production_id'] = self.raw_material_production_id.id
    #
    #     if self.production_id and not self.raw_material_production_id:
    #         res['context']['default_production_id'] = self.production_id.id
    #
    #     return res

    @api.multi
    def button_validate(self):
        result = super(StockPicking, self).button_validate()
        for order in self:
            if order.production_id:
                if len(order.production_id.workorder_ids) == 0:
                    raise UserError(_("Belum Ada Proses Work Order Yang Berjalan"))
           

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















