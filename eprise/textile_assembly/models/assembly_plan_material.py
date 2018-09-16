from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class AssemblyPlanMaterial(models.Model):
    _name = 'assembly.plan.material'
    _description = 'Assembly Plan Material'

    @api.one
    @api.depends('product_qty', 'total_quantity')
    def compute_amount_qty(self):
        if self.total_quantity:
            self.amount_qty = round(self.total_quantity * self.product_qty) / self.total_ratio

    @api.one
    @api.depends('qty_available', 'amount_qty')
    def compute_qty_to_po(self):
        qty = 0.0
        if self.amount_qty > self.qty_available:
            qty += self.amount_qty - self.qty_available
            self.qty_to_po = qty
        else:
            self.qty_to_po = 0.0

    @api.one
    @api.depends('plan_id.location_id', 'product_id.qty_available')
    def compute_qty_available(self):
        for record in self:
            if record.plan_id.location_id:
                record.qty_available = record.get_product_availability(record.plan_id.location_id, record.product_id)


    cancelled = fields.Boolean(
        string="Cancelled", readonly=True, default=False, copy=False)

    plan_id = fields.Many2one(comodel_name="assembly.plan", string="Plans", index=True)
    plan_material_ids = fields.Many2many(
        'assembly.prod.bom.line',
        'assembly_prod_bom_line_plan_rel',
        'bom_line_id', 'order_line_id',
        string='Assembly Plan materials', readonly=True, copy=False)
    sequence = fields.Integer('Sequence', default=1)
    product_id = fields.Many2one(comodel_name="product.product", string="Products", index=True)
    product_qty = fields.Float(string="Quantity", default=0.0, digits=dp.get_precision('Product Unit of Measure'),
                               store=True)
    product_uom_id = fields.Many2one(comodel_name="product.uom", string="UoM")
    qty_available = fields.Float(string="Available Quantity",
                                 compute='compute_qty_available',
                                 digits=dp.get_precision('Product Unit of Measure'))
    qty_to_po = fields.Float(string="Qty To PO",
                             compute='compute_qty_to_po', default=0.0,
                             digits=dp.get_precision('Product Unit of Measure'), store=True)

    total_ratio = fields.Float(string="Total Ratio", help="Jumlah Berdasarkan Ratio")
    total_quantity = fields.Float(string="Total Quantity", default=0.0, digits=dp.get_precision('Product Unit of Measure'),
                                  store=True, help="Jumlah Plan Produksi Awal")
    amount_qty = fields.Float(string="Expected Quantity", default=0.0, digits=dp.get_precision('Product Unit of Measure'),
                              store=True, compute="compute_amount_qty")
    state = fields.Selection(related='plan_id.state', store=True)

    @api.multi
    def do_cancel(self):
        """Actions to perform when cancelling a purchase request line."""
        self.write({'cancelled': True})

    @api.multi
    def do_uncancel(self):
        """Actions to perform when uncancelling a purchase request line."""
        self.write({'cancelled': False})

    @api.multi
    def get_product_availability(self, location, product):
        quant_obj = self.env['stock.quant']
        amount = 0.0
        sublocation_ids = self.env['stock.location'].search([('id', 'child_of', location.id)])
        for line in sublocation_ids:
            quant_ids = quant_obj.search(
                [('location_id', '=', line.id), ('product_id', '=', product.id)])
            if quant_ids:
                for quant in quant_ids:
                    amount += quant.quantity
        return amount


