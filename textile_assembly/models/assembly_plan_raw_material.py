import math
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round


class AssemblyPlanRawMaterial(models.Model):
    _name = 'assembly.plan.raw.material'
    _rec_name = 'product_id'
    _description = 'Assembly Plan Material'

    plan_id = fields.Many2one(comodel_name="assembly.plan", string="Plan Order",
                              ondelete='cascade', index=True)
    sequence = fields.Integer('Sequence', default=1)
    product_id = fields.Many2one(comodel_name="product.product", string="Products", index=True)
    product_qty = fields.Float('Quantity', default=0.0, digits=dp.get_precision('Product Unit of Measure'))
    product_uom_id = fields.Many2one(comodel_name="product.uom", string="UoM")
    qty_available = fields.Float('OnHand', digits=dp.get_precision('Product Unit of Measure'))
    total_ratio = fields.Float('Total Ratio', help="Jumlah Berdasarkan Ratio")
    qty_to_plan = fields.Float('Exp Consu Plan',
                               digits=dp.get_precision('Product Unit of Measure'),
                               help="Total Yang Diharapkan Untuk Kebutuhan Material Yang Akan Diproduksi")
    qty_to_actual = fields.Float('Exp Consu Actual',
                                 digits=dp.get_precision('Product Unit of Measure'))

    qty_final = fields.Float(string="To Be Produce Qty", default=0.0, digits=dp.get_precision('Product Unit of Measure'),
                             help="Berapa Unit Produk Yang Jadi DiProduksi, Maksimum Kapasitas")

    total_actual_quantity = fields.Float(string="Maximum Potensial", default=0.0,
                                         digits=dp.get_precision('Product Unit of Measure'),
                                         compute="_compute_total_actual_quantity", store=True)
    price_unit = fields.Float('Unit Price', digits=dp.get_precision('Product Price'))
    price_subtotal = fields.Float('Subtotal', digits=dp.get_precision('Account'),
                                  compute="_compute_price_subtotal")
    price_subtotal_actual = fields.Float(string="Sub Total", digits=dp.get_precision('Account'),
                                         compute="_compute_price_subtotal")

    attribute_id = fields.Many2one(comodel_name="product.attribute.value", string="Variants")

    needs_lots = fields.Boolean('Tracking', compute='_compute_needs_lots')
    line_ids = fields.One2many(comodel_name="assembly.plan.raw.material.line", inverse_name="line_id", string="Lots")
    state = fields.Selection(related='plan_id.state')

    lot_ids = fields.One2many(comodel_name="stock.production.lot",
                              inverse_name="raw_material_plan_id", string="Lots Of Product")
    need_procurement = fields.Boolean(string="Need Procurment", readonly=True, compute="_compute_need_procurement")
    date_planned_start = fields.Datetime('Deadline Start', copy=False, index=True,
                                         related="plan_id.date_planned_start")
    # Tambahan untuk report
    # qty_consumed = fields.Float(string="Qty Consumed", digits=dp.get_precision('Product Unit of Measure'),
    #                             readonly=True)
    # qty_used = fields.Float(string="Qty Consumed", digits=dp.get_precision('Product Unit of Measure'), readonly=True)
    # qty_reject = fields.Float(string="Qty Reject", digits=dp.get_precision('Product Unit of Measure'), readonly=True)
    # qty_return = fields.Float(string="Qty Return", digits=dp.get_precision('Product Unit of Measure'), readonly=True)
    # qty_differ = fields.Float(string="Qty Differ", digits=dp.get_precision('Product Unit of Measure'),
    #                           compute="_compute_qty_differ", store=True)

    @api.multi
    @api.depends('qty_available', 'product_qty',
                 'total_ratio')
    def _compute_total_actual_quantity(self):
        for material in self:
            if material.qty_available:
                result_qty = material.qty_available / material.product_qty
                material.total_actual_quantity = math.ceil(result_qty)

        return True

    @api.multi
    @api.depends('product_qty', 'total_qty_to_plan', 'total_ratio')
    def _compute_amount_qty(self):
        for material in self:
            if material.total_qty_to_plan:
                result_qty = (material.product_qty / material.total_ratio) * material.total_qty_to_plan
                material.qty_to_plan = float_round(result_qty, precision_rounding=material.product_id.uom_id.rounding,
                                                   rounding_method='UP')
        return True

    @api.multi
    @api.depends('price_unit',
                 'qty_to_actual',
                 'product_qty')
    def _compute_price_subtotal(self):
        for material in self:
            material.price_subtotal = material.product_qty * material.price_unit
            material.price_subtotal_actual = material.qty_to_actual * material.price_unit

        return True

    @api.multi
    @api.depends('qty_available', 'qty_to_plan')
    def _compute_need_procurement(self):
        for material in self:
            if material.qty_to_plan > material.qty_available:
                material.need_procurement = True
            else:
                material.need_procurement = False

    # @api.multi
    # @api.depends('qty_consumed',
    #              'qty_used')
    # def _compute_qty_differ(self):
    #     for material in self:
    #         if material.qty_used != material.qty_consumed:
    #             material.qty_differ = material.qty_consumed - material.qty_used
    #     return True

    @api.multi
    def check_lot(self):
        self.ensure_one()
        for order in self:
            if order.needs_lots:
                lot_ids = order.lot_ids.filtered(lambda x: x.product_id.id == order.product_id.id)
                if not lot_ids:
                    lots = self.env['stock.production.lot'].search([('product_id', '=', order.product_id.id)])
                    lots.write({'raw_material_plan_id': order.id})
                else:
                    return self.env['stock.production.lot']

    @api.multi
    def get_lot(self):
        for order in self:
            lot_domain = self.env['stock.production.lot'].search([('product_id', '=', order.product_id.id)])
            for lot in lot_domain:
                if lot and lot.filtered(lambda x: x.product_qty > 0):
                    value = {'lot_id': lot.id,
                             'quantity': lot.product_qty,
                             'line_id': order.id}

                    order.line_ids.create(value)

    @api.depends('product_id.tracking')
    def _compute_needs_lots(self):
        for move in self:
            move.needs_lots = move.product_id.tracking != 'none'


class AssemblyPlanRawMaterialLine(models.Model):
    _name = 'assembly.plan.raw.material.line'
    _description = 'Line Contains Lot'

    line_id = fields.Many2one(comodel_name="assembly.plan.raw.material", string="Raw Order",
                              ondelete='cascade', index=True)

    lot_id = fields.Many2one(comodel_name="stock.production.lot", string="Lot/Serial Number")
    quantity = fields.Float(string="Quantity",digits=dp.get_precision('Product Unit of Measure'))


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    raw_material_plan_id = fields.Many2one(comodel_name="assembly.plan.raw.material", string="Raw Material Plan")









