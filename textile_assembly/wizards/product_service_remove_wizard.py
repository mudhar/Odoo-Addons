from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class ProductServiceRemoveWizard(models.TransientModel):
    _name = 'mrp_workorder.product_service_remove.wizard'
    _description = 'Wizard Buat Menghapus Product Service Di Dalam Workorder'

    work_order_id = fields.Many2one(comodel_name="mrp.workorder", string="Work Order Reference")
    production_id = fields.Many2one(comodel_name="mrp.production", string="Production Reference")

    product_service_id = fields.Many2one(comodel_name="product.product", string="Biaya Produksi")

    @api.model
    def default_get(self, fields_list):
        res = super(ProductServiceRemoveWizard, self).default_get(fields_list)
        if 'work_order_id' in fields_list and not res.get('work_order_id') and self._context.get(
                'active_model') == 'mrp.workorder' and self._context.get('active_id'):
            res['work_order_id'] = self._context['active_id']

        if 'production_id' in fields_list and not res.get('production_id') and res.get('work_order_id'):
            res['production_id'] = self.env['mrp.workorder'].browse(res['work_order_id']).production_id.id

        return res

    @api.multi
    def check_purchase_product_service(self):
        work_order_object = self.env['mrp.workorder']
        for purchase_ids in work_order_object.search(
                [('production_id', '=', self.production_id.id)]).mapped('po_ids'):
            for purchase in purchase_ids.mapped('order_line').filtered(lambda x: x.product_id.id == self.product_service_id.id):
                if purchase.state != 'cancel':
                    raise UserError(_("Product %s Sudah Kebentuk Purchase Order\n"
                                      "Batalkan PO %s Yang Terdapat Product ini\n"
                                      "Apabila Anda Ingin Menghapus Product Dari Work Order")
                                    % (self.product_service_id.display_name, purchase.order_id.display_name))

    @api.multi
    def button_confirm(self):
        for order in self:
            self.check_purchase_product_service()
            work_order_ids = self.env['mrp.workorder'].search(
                [('production_id', '=', order.production_id.id)])
            for work_order in work_order_ids.mapped('product_service_ids'):
                if work_order.product_id.id != order.product_service_id.id:
                    continue

                if work_order.product_id.id == order.product_service_id.id:
                    work_order.unlink()
            assembly_plan_id = order.production_id.mapped('assembly_plan_id')
            if assembly_plan_id:
                for plan in assembly_plan_id.cmt_service_ids.filtered(
                        lambda x: x.product_id.id == order.product_service_id.id):
                    plan.unlink()

            assembly_id = order.production_id.assembly_plan_id.mapped('assembly_id')
            if assembly_id:
                for assembly in assembly_id.cmt_service_ids.filtered(
                        lambda x: x.product_id.id == order.product_service_id.id):
                    assembly.unlink()

        return {'type': 'ir.actions.act_window_close'}
