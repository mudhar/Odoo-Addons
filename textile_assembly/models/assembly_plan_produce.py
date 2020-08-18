from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class AssemblyPlanProduce(models.Model):
    _name = 'assembly.plan.produce'
    _rec_name = 'attribute_id'
    _description = 'Total Quantity To Produce'

    plan_id = fields.Many2one(comodel_name="assembly.plan", string="Plan Order",
                              ondelete='cascade', index=True)
    attribute_id = fields.Many2one(comodel_name="product.attribute.value", string="Description")
    quantity_plan = fields.Float(string="PLAN Quantity To Produce",
                                 digits=dp.get_precision('Product Unit of Measure'))
    quantity_actual = fields.Float(string="Revised Quantity To Produce",
                                   digits=dp.get_precision('Product Unit of Measure'))
    quantity_maximum = fields.Float(string="Max Qty To Produce", compute="_compute_maximum_quantity",
                                    digits=dp.get_precision('Product Unit of Measure'))
    original_quantity_actual = fields.Float(string="Orignal ACTUAL Quantity To Produce",
                                            digits=dp.get_precision('Product Unit of Measure'))
    original_quantity_plan = fields.Float(string="Orignal Plan Quantity To Produce",
                                          digits=dp.get_precision('Product Unit of Measure'),
                                         )


    state = fields.Selection(related='plan_id.state')
    # Untuk Mengecek Apabila Terdapat Bahan Baku Membutuhkan Stok Tambahan -> Button Procurement(tampil)
    # Maka field quantity_actual Tidak Dapat Diisi Terlebih Dahulu(readonly) Dan Begitu Sebaliknya
    editable_quantity = fields.Boolean(string="Quantity Editable", compute="_compute_status_procurement")

    @api.multi
    @api.depends('plan_id',
                 'plan_id.check_raw_procurement',
                 'plan_id.check_cmt_procurement')
    def _compute_status_procurement(self):
        for order in self:
            order.editable_quantity = order.plan_id.check_raw_procurement or order.plan_id.check_cmt_procurement


    @api.multi
    @api.onchange('quantity_actual')
    def onchange_quantity_actual(self):
        for order in self:
            if order.quantity_actual > order.quantity_maximum:
                raise UserError(_("Maksimum Yang Bisa Diproduksi Adalah %s") % order.quantity_maximum)

    @api.multi
    @api.depends('plan_id.raw_line_ids',
                 'plan_id.raw_line_ids.total_actual_quantity')
    def _compute_maximum_quantity(self):
        for order in self:
            if order.attribute_id:
                quantity_max = []
                for raw in order.plan_id.raw_line_ids.filtered(lambda x: x.attribute_id.id == order.attribute_id.id):
                    quantity_max.append(raw.total_actual_quantity)
                if quantity_max and len(quantity_max) > 1:
                    order.quantity_maximum = max(quantity_max)
                else:
                    order.quantity_maximum = quantity_max[0]
        return {}













