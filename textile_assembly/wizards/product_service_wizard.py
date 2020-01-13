from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class ProductServiceWizard(models.TransientModel):
    _name = 'mrp_workorder.product_service.wizard'
    _description = 'Wizard Buat Menambahkan Product Service Di Dalam Workorder'

    work_order_id = fields.Many2one(comodel_name="mrp.workorder", string="Work Order Reference")
    production_id = fields.Many2one(comodel_name="mrp.production", string="Production Reference")

    product_service_id = fields.Many2one(comodel_name="product.product", string="Biaya Produksi")
    product_qty = fields.Float(string="Quantity", digits=dp.get_precision('Product Unit of Measure'),
                               default=1.0)
    product_uom_id = fields.Many2one(comodel_name="product.uom", string="UoM", related="product_service_id.uom_id")
    price_unit = fields.Float(string="Unit Price", digits=dp.get_precision('Product Price'))

    @api.model
    def default_get(self, fields_list):
        res = super(ProductServiceWizard, self).default_get(fields_list)
        if 'work_order_id' in fields_list and not res.get('work_order_id') and self._context.get(
                'active_model') == 'mrp.workorder' and self._context.get('active_id'):
            res['work_order_id'] = self._context['active_id']

        if 'production_id' in fields_list and not res.get('production_id') and res.get('work_order_id'):
            res['production_id'] = self.env['mrp.workorder'].browse(res['work_order_id']).production_id.id

        return res

    @api.multi
    def button_confirm(self):
        for order in self:
            work_order_ids = self.env['mrp.workorder'].search(
                [('production_id', '=', order.production_id.id)])
            service_ids = work_order_ids.mapped('product_service_ids').mapped('work_order_id')
            for service in service_ids:
                if service.id:
                    product_ids = order.action_generate_new_product_ids()
                    product_ids.update({'work_order_id': service.id})
                    self.env['mrp.workorder.service.line'].create(product_ids)
            order.generate_new_product_to_assembly()
            order.generate_new_product_to_plan()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def generate_new_product_to_assembly(self):
        cmt_services = self.env['assembly.cmt.product.service']
        assembly_id = self.work_order_id.production_id.assembly_plan_id.mapped('assembly_id')
        new_products = self.action_generate_new_product_ids()
        if assembly_id:
            new_products.update({'assembly_id': assembly_id.id})
            cmt_services |= self.env['assembly.cmt.product.service'].create(new_products)

        return cmt_services

    @api.multi
    def generate_new_product_to_plan(self):
        plan_services = self.env['assembly.plan.services']
        plan_id = self.work_order_id.production_id.mapped('assembly_plan_id')
        new_products = self.action_generate_new_product_ids()
        if plan_id:
            new_products.update({
                                 'plan_id': plan_id.id})
            plan_services |= self.env['assembly.plan.services'].create(new_products)

        return plan_services

    @api.multi
    def action_generate_new_product_ids(self):
        return {
            'product_id': self.product_service_id.id,
            'product_qty': self.product_qty,
            'product_uom_id': self.product_uom_id.id,
            'price_unit': self.price_unit,
        }
