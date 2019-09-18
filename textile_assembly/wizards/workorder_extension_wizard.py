import math
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp


class WorkOrderExtensionWizard(models.TransientModel):
    _name = 'workorder.extension.wizard'
    _description = 'Wizard Buat Menambahkan WorkOrder Di Dalam Workorder'

    previous_workorder_id = fields.Many2one(comodel_name="mrp.workorder", string="Previous Workorder")
    workcenter_id = fields.Many2one(comodel_name="mrp.workcenter", string="Work Center")
    product_id = fields.Many2one(comodel_name="product.template", string="Product")
    partner_id = fields.Many2one(comodel_name="res.partner", string="CMT Vendor")

    product_service_id = fields.Many2one(comodel_name="product.product", string="Biaya Produksi")
    product_qty = fields.Float(string="Quantity", digits=dp.get_precision('Product Unit of Measure'),
                               default=1.0)
    product_uom_id = fields.Many2one(comodel_name="product.uom", string="UoM", related="product_service_id.uom_id")
    price_unit = fields.Float(string="Unit Price", digits=dp.get_precision('Product Price'))

    bom_id = fields.Many2one(comodel_name="mrp.bom", string="Bom")
    time_cycle = fields.Float(string="Duration", default=60)

    is_new_product = fields.Boolean(string="Tambah Biaya Produksi")

    @api.model
    def default_get(self, fields_list):
        res = super(WorkOrderExtensionWizard, self).default_get(fields_list)
        if 'previous_workorder_id' in fields_list and not res.get('previous_workorder_id') and self._context.get(
                'active_model') == 'mrp.workorder' and self._context.get('active_id'):
            res['previous_workorder_id'] = self._context['active_id']

        if 'bom_id' in fields_list and not res.get('bom_id') and res.get('previous_workorder_id'):
            res['bom_id'] = self.env['mrp.workorder'].browse(res['previous_workorder_id']).production_id.bom_id.id

        if 'product_id' in fields_list and not res.get('product_id') and res.get('previous_workorder_id'):
            res['product_id'] = self.env['mrp.workorder'].browse(res['previous_workorder_id']).product_template_id.id

        if 'partner_id' in fields_list and not res.get('partner_id') and res.get('previous_workorder_id'):
            res['partner_id'] = self.env['mrp.workorder'].browse(res['previous_workorder_id']).partner_id.id

        return res

    @api.multi
    def button_confirm(self):
        for order in self:
            dict_sequence = {}
            created_workorder = order.action_create_workorder()

            if order.is_new_product:
                workorder_ids = self.env['mrp.workorder'].search(
                    [('production_id', '=', order.previous_workorder_id.production_id.id)]).filtered(
                    lambda x: x.id != created_workorder.id)
                service_ids = workorder_ids.mapped('product_service_ids').mapped('work_order_id')
                for service in service_ids:
                    if service.id:
                        product_ids = order.action_generate_new_product_ids()
                        product_ids.update({'work_order_id': service.id})
                        self.env['mrp.workorder.service.line'].create(product_ids)
                order.generate_new_product_to_assembly()

            if created_workorder:
                if order.is_new_product:
                    new_products = created_workorder.mapped('product_service_ids')
                    product_value = order.action_generate_new_product_ids()
                    product_value.update({'work_order_id': created_workorder.id})
                    new_products |= self.env['mrp.workorder.service.line'].create(product_value)

                if created_workorder.id and created_workorder.next_work_order_id.id not in dict_sequence:
                    dict_sequence[created_workorder.id] = created_workorder.sequence
                    dict_sequence[created_workorder.next_work_order_id.id] = created_workorder.next_work_order_id.sequence

                if created_workorder.sequence > created_workorder.next_work_order_id.sequence:
                    created_workorder.update({'sequence': dict_sequence[created_workorder.next_work_order_id.id]})
                    created_workorder.next_work_order_id.update({'sequence': dict_sequence[created_workorder.id]})

                created_workorder.next_work_order_id.mapped('qc_ids').write({'is_updated_from_prev_workorder': False})

                order.previous_workorder_id.write({'workorder_created': True,
                                                   'state': 'pending'})

        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def generate_new_product_to_assembly(self):
        cmt_services = self.env['assembly.cmt.product.service']
        assembly_id = self.previous_workorder_id.production_id.assembly_plan_id.mapped('assembly_id')
        new_products = self.action_generate_new_product_ids()
        new_products.update({'assembly_id': assembly_id.id})
        cmt_services |= self.env['assembly.cmt.product.service'].create(new_products)
        return cmt_services

    @api.multi
    def action_generate_new_product_ids(self):
        return {
                'product_id': self.product_service_id.id,
                'product_qty': self.product_qty,
                'product_uom_id': self.product_uom_id.id,
                'price_unit': self.price_unit,
            }

    @api.multi
    def action_create_workorder(self):
        workorders = self.env['mrp.workorder']
        for order in self:
            quantity = order.product_id.uom_id._compute_quantity(order.previous_workorder_id.qty_production,
                                                              order.bom_id.product_uom_id) / order.bom_id.product_qty
            boms, lines = order.bom_id.explode_template(order.product_id, quantity)

            new_workorder = order._generate_new_workorder(boms)
            order.generate_product_services(new_workorder)

            order.generate_product_variants(new_workorder)
            if new_workorder:
                new_workorder.write({'next_work_order_id': order.previous_workorder_id.next_work_order_id.id})
                order.previous_workorder_id.write({'next_work_order_id': new_workorder.id})

            workorder_ids = self.env['mrp.workorder'].search(
                [('production_id', '=', new_workorder.production_id.id)]).sorted(key=lambda x: not x.next_work_order_id and x.sequence)

            for count, workorder_id in enumerate(workorder_ids):
                workorder_id.update({'sequence': count + 1})

            workorders += new_workorder
        return workorders

    def _generate_new_workorder(self, exploded_boms):
        workorders = self.env['mrp.workorder']
        for bom, bom_data in exploded_boms:
            bom_qty = bom_data['quantity']
            # create workorder
            cycle_number = math.ceil(bom_qty / self.workcenter_id.capacity)
            duration_expected = (self.workcenter_id.time_start +
                                 self.workcenter_id.time_stop +
                                 cycle_number * self.time_cycle * 100.0 / self.workcenter_id.time_efficiency)

            workorder = workorders.create({
                'name': self.workcenter_id.name,
                'partner_id': self.partner_id.id,
                'is_cutting': self.workcenter_id.is_cutting,
                'production_id': self.previous_workorder_id.production_id.id,
                'workcenter_id': self.workcenter_id.id,
                'duration_expected': duration_expected,
                'state': 'pending',
                'qty_producing': self.previous_workorder_id.qty_producing,
                'capacity': self.workcenter_id.capacity,
            })

            workorders += workorder

            return workorders

    def generate_product_services(self, work_order_id):
        service_ids = self.env['mrp.workorder.service.line']
        for order in self.previous_workorder_id.product_service_ids:
            services = service_ids.create({
                'product_id': order.product_id.id,
                'product_qty': order.product_qty,
                'product_uom_id': order.product_uom_id.id,
                'price_unit': order.price_unit,
                'work_order_id': work_order_id.id,
            })
            service_ids += services
        return service_ids

    def generate_product_variants(self, work_order_id):
        variants = self.env['mrp.workorder.qc.line']

        for order in self.previous_workorder_id.qc_ids:
            variant = variants.create({
                'product_id': order.product_id.id,
                'product_qty': order.qc_good if order.state == 'done' else order.product_qty,
                'product_uom_id': order.product_uom_id.id,
                'is_updated_from_prev_workorder': True if order.state == 'done' else False,
                'ratio': order.ratio,
                'qc_id': work_order_id.id
            })
            variants += variant
        return variants

