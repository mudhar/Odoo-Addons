import math
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.model
    def _get_default_picking_type_production(self):
        return self.env.ref('textile_assembly.picking_cmt_produce').id

    @api.model
    def _get_default_picking_type_consume(self):
        return self.env.ref('textile_assembly.picking_cmt_consume').id

    partner_id = fields.Many2one(comodel_name="res.partner", string="CMT Vendor")
    assembly_plan_id = fields.Many2one(comodel_name="assembly.plan", string="Assembly Plan", readonly=True, copy=True)
    variant_ids = fields.One2many(comodel_name="mrp.production.variant", inverse_name="production_id",
                                  string="Variant On Hand", copy=True)

    # picking
    picking_type_production = fields.Many2one(
        'stock.picking.type', 'Operation Type CMT Production', default=_get_default_picking_type_production)
    picking_type_consume = fields.Many2one(
        'stock.picking.type', 'Operation Type CMT Consume', default=_get_default_picking_type_consume)
    picking_count = fields.Integer(string="#Picking Production", compute="_compute_picking_count")
    picking_raw_count = fields.Integer(string="#Picking Consume", compute="_compute_picking_raw_count")
    picking_raw_ids = fields.One2many(comodel_name="stock.picking", inverse_name="raw_material_production_id",
                                      string="Picking Consumed Products", copy=False,
                                      states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    picking_finished_product_ids = fields.One2many(comodel_name="stock.picking", inverse_name="production_id",
                                                   string="Picking Finished Products", copy=False,
                                                   states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    # Work Order
    check_work_order_done = fields.Boolean(string="Check Work Order Done", compute="_get_produced_qty",
                                           help="Informasi Untuk Mengecek Status Work Order Yang Done")
    # Begin override field
    product_id = fields.Many2one(
        required=False)
    product_uom_id = fields.Many2one(required=False)
    # End override field
    product_template_id = fields.Many2one(comodel_name="product.template", string="Product",
                                          domain=[('type', 'in', ['product', 'consu'])],
                                          readonly=True, states={'confirmed': [('readonly', False)]})
    backdate_finished = fields.Datetime('End Date', copy=False, index=True)

    def _compute_picking_count(self):
        read_group_res = self.env['stock.picking'].read_group([('production_id', 'in', self.ids)],
                                                              ['production_id'],
                                                              ['production_id'])
        mapped_data = dict([(data['production_id'][0], data['production_id_count']) for data in read_group_res])
        for record in self:
            record.picking_count = mapped_data.get(record.id, 0)

    def _compute_picking_raw_count(self):
        read_group_res = self.env['stock.picking'].read_group([('raw_material_production_id', 'in', self.ids)],
                                                              ['raw_material_production_id'],
                                                              ['raw_material_production_id'])
        mapped_data = dict([(data['raw_material_production_id'][0],
                             data['raw_material_production_id_count']) for data in read_group_res])
        for record in self:
            record.picking_raw_count = mapped_data.get(record.id, 0)

    @api.depends('workorder_ids.state', 'move_finished_ids', 'is_locked')
    def _get_produced_qty(self):
        for production in self:
            if production.assembly_plan_id:
                done_moves = production.move_finished_ids.filtered(lambda x: x.state == 'done' and
                                                                             x.product_id.product_tmpl_id.id ==
                                                                             production.product_template_id.id)
                qty_produced = sum(done_moves.mapped('quantity_done'))

                if any([x.state not in ('done', 'cancel') for x in production.workorder_ids]):
                    wo_done = False
                else:
                    wo_done = True
                production.check_to_done = production.is_locked and done_moves and (
                        production.state not in ('done', 'cancel')) and wo_done
                production.qty_produced = qty_produced
                production.check_work_order_done = wo_done
            else:
                return super(MrpProduction, self)._get_produced_qty()

    # Original Method mrp.production
    @api.multi
    def action_assign(self):
        for production in self:
            if production.assembly_plan_id:
                return production.picking_raw_ids.action_assign()
            else:
                return super(MrpProduction, self).action_assign()

    @api.multi
    def action_cancel(self):
        for production in self:
            move_consumed = production.move_raw_ids.filtered(
                lambda x: (not x.scrapped and not x.returned_picking) and x.raw_material_production_id)
            move_returned = production.move_raw_ids.filtered(
                lambda x: (not x.scrapped and x.returned_picking) and x.raw_material_production_id)

            if move_consumed:
                if (move_consumed and not move_returned) and all(
                        move.state == 'done' for move in move_consumed):
                    raise UserError(_("Bahan Baku Sudah Terkonsumsi, Apabila Anda Ingin Membatalkan Manufacturing Order"
                                      "\n Anda Harus Mengembalikan Bahan Baku Yang Terkonsumsi Ke Gudang"
                                      "\n Anda Dapat Melakukan Tersebut Pada Halaman Picking Consume"
                                      "\n Dengan Mengklik Tombol Return"))
                elif (move_consumed and move_returned) and all(
                        move.state != 'done' for move in move_returned
                ):
                    raise UserError(_("Status Bahan Baku Yang Direturn Belum Selesai Ditransfer"))
                production.assembly_plan_id._action_cancel()

        return super(MrpProduction, self).action_cancel()

    @api.multi
    def button_mark_done(self):
        self.ensure_one()
        # self.post_inventory()
        if self.assembly_plan_id:
            return self.action_mark_done()
        else:
            return super(MrpProduction, self).button_mark_done()
        # for production in self:
        #     if production.assembly_plan_id:
        #         return production.action_mark_done()
        #     else:
        #         return super(MrpProduction, self).button_mark_done()

    @api.multi
    def action_mark_done(self):
        self.ensure_one()
        for wo in self.workorder_ids:
            if wo.time_ids.filtered(
                    lambda x: (not x.date_end) and (x.loss_type in ('productive', 'performance'))):
                raise UserError(_('Work order %s is still running') % wo.name)

        if not self.backdate_finished:
            raise UserError(_("Date End Wajib Diisi"))
        moves_to_cancel = (self.move_raw_ids | self.move_finished_ids).filtered(
            lambda x: x.state not in ('done', 'cancel'))
        moves_to_cancel._action_cancel()
        self.write({'state': 'done', 'date_finished': self.backdate_finished})
        return self.write({'state': 'done'})

    @api.multi
    def _generate_moves(self):
        for production in self:
            if production.assembly_plan_id:
                return production.generate_plan_moves()
            else:
                return super(MrpProduction, self)._generate_moves()

    @api.multi
    def generate_plan_moves(self):
        for production in self:
            # production._generate_finished_picking()
            factor = production.product_uom_id._compute_quantity(production.product_qty,
                                                                 production.bom_id.product_uom_id) / production.bom_id.product_qty
            boms, lines = production.bom_id.explode_template(production.product_template_id, factor)
            # Raw Material Product
            move_raw = production._generate_plan_raw_moves(lines)
            raw_picking = production._generate_picking_raw_moves()
            move_raw.write({
                'picking_id': raw_picking.id,
                'picking_type_id': raw_picking.picking_type_id.id
            })

            # Check for all draft moves whether they are mto or not
            production._adjust_procure_method()
        return True

    def _generate_picking_raw_moves(self):
        picking_obj = self.env['stock.picking']
        done = self.env['stock.picking'].browse()
        for order in self:
            pickings = order.picking_raw_ids.filtered(
                lambda x: x.raw_material_production_id and x.state not in ('done', 'cancel'))
            if not pickings:
                if order.routing_id:
                    routing = order.routing_id
                else:
                    routing = order.bom_id.routing_id
                if routing and routing.location_id:
                    source_location = routing.location_id
                else:
                    source_location = order.location_src_id
                res = {
                    'picking_type_id': order.picking_type_consume.id,
                    'partner_id': order.partner_id.id or False,
                    'location_id': source_location.id,
                    'location_dest_id': order.product_template_id.property_stock_production.id,
                    'origin': ''.join('%s:%s' % (order.name, order.origin)),
                    'raw_material_production_id': order.id,
                    'group_id': order.procurement_group_id.id,
                    'company_id': order.company_id.id,
                    'product_select_type': 'materials'
                }
                done += picking_obj.create(res)
            else:
                done += pickings[0]
        return done

    # def _generate_raw_move(self, bom_line, line_data):
    def _generate_plan_raw_moves(self, exploded_lines):
        self.ensure_one()
        moves = self.env['stock.move']
        for bom_line, line_data in exploded_lines:
            moves += self._generate_plan_raw_move(bom_line, line_data)
        return moves

    def _generate_plan_raw_move(self, bom_line, line_data):
        # quantity = line_data['qty']
        # qty = line_data['original_qty']
        quantity = line_data['quantity']
        qty = line_data['original_qty']
        # alt_op needed for the case when you explode phantom bom and all the lines will be consumed in the operation given by the parent bom line
        alt_op = line_data['parent_line'] and line_data['parent_line'].operation_id.id or False
        if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom':
            return self.env['stock.move']
        if bom_line.product_id.type not in ['product', 'consu']:
            return self.env['stock.move']
        if self.routing_id:
            routing = self.routing_id
        else:
            routing = self.bom_id.routing_id
        if routing and routing.location_id:
            source_location = routing.location_id
        else:
            source_location = self.location_src_id
        original_quantity = (qty - self.qty_produced) or 1.0

        data = {
            'sequence': bom_line.sequence,
            'partner_id': self.partner_id.id,
            'name': ''.join('%s:%s' % (self.name, bom_line.product_id.display_name)),
            'date': self.date_planned_start,
            'date_expected': self.date_planned_start,
            'bom_line_id': bom_line.id,
            'product_id': bom_line.product_id.id,
            'product_uom_qty': quantity,
            'product_uom': bom_line.product_uom_id.id,
            'location_id': source_location.id,
            'location_dest_id': self.product_template_id.property_stock_production.id,
            'raw_material_production_id': self.id,
            'company_id': self.company_id.id,
            'operation_id': bom_line.operation_id.id or alt_op,
            'price_unit': bom_line.product_id.standard_price,
            'procure_method': 'make_to_stock',
            'origin': ''.join('%s:%s' % (self.name, self.origin)),
            'warehouse_id': source_location.get_warehouse().id,
            'group_id': self.procurement_group_id.id,
            'propagate': self.propagate,
            'unit_factor': quantity / original_quantity,
        }
        return self.env['stock.move'].create(data)

    # Create Work Order
    @api.multi
    def button_plan(self):
        for production in self:
            if production.assembly_plan_id:
                return production.action_work_order_assembly()
            else:
                return super(MrpProduction, self).button_plan()

    @api.multi
    def _check_move_consume_state(self):
        move_consumed = self.move_raw_ids.filtered(
            lambda x: (not x.scrapped and not x.returned_picking) and x.raw_material_production_id)
        move_returned = self.move_raw_ids.filtered(
            lambda x: (not x.scrapped and x.returned_picking) and x.raw_material_production_id)
        if move_consumed and not move_returned and any(
                move.state not in ['done', 'cancel'] for move in move_consumed):
            raise UserError(_("Produk Yang Dikonsumsi Belum Selesai Statusnya"))
        elif move_consumed and move_returned and all(
                move.state != 'done' for move in move_returned):
            raise UserError(_("Anda Tidak Dapat Melanjutkan Plan\n"
                              "Anda Sedang Melakukan Return Produk Ke Gudang\n"))

    @api.multi
    def action_work_order_assembly(self):
        # self.action_update_plan_consumed()
        orders_to_plan = self.filtered(lambda order: order.routing_id and (
                not order.product_id and order.state == 'confirmed'))
        if orders_to_plan:
            for order in orders_to_plan:
                order._check_move_consume_state()
                quantity = order.product_uom_id._compute_quantity(order.product_qty,
                                                                  order.bom_id.product_uom_id) / order.bom_id.product_qty
                boms, lines = order.bom_id.explode_template(order.product_template_id, quantity)
                order.generate_workorders(boms)

            return orders_to_plan.write({'state': 'planned'})

    @api.multi
    def generate_workorders(self, exploded_boms):
        workorders = self.env['mrp.workorder']
        original_one = False
        for bom, bom_data in exploded_boms:
            # If the routing of the parent BoM and phantom BoM are the same, don't recreate work orders, but use one master routing
            if bom.routing_id.id and (
                    not bom_data['parent_line'] or bom_data['parent_line'].bom_id.routing_id.id != bom.routing_id.id):
                temp_workorders = self.workorders_create(bom, bom_data)
                workorders += temp_workorders
                if temp_workorders:  # In order to avoid two "ending work orders"
                    if original_one:
                        temp_workorders[-1].next_work_order_id = original_one
                    original_one = temp_workorders[0]
        return workorders

    def workorders_create(self, bom, bom_data):
        """
        :param bom: in case of recursive boms: we could create work orders for child
                    BoMs
        """
        workorders = self.env['mrp.workorder']
        bom_qty = bom_data['quantity']


        # Initial qty producing
        if self.product_template_id.tracking == 'serial':
            quantity = 1.0
        else:
            quantity = self.product_qty - sum(self.move_finished_ids.mapped('quantity_done'))
            quantity = quantity if (quantity > 0) else 0

        for operation in bom.routing_id.operation_ids:
            # create workorder
            cycle_number = math.ceil(bom_qty / operation.workcenter_id.capacity)  # TODO: float_round UP
            duration_expected = (operation.workcenter_id.time_start +
                                 operation.workcenter_id.time_stop +
                                 cycle_number * operation.time_cycle * 100.0 / operation.workcenter_id.time_efficiency)
            workorder = workorders.create({
                'name': operation.name,
                'partner_id': self.partner_id.id,
                'is_cutting': operation.workcenter_id.is_cutting,
                'production_id': self.id,
                'sequence': operation.sequence,
                'workcenter_id': operation.workcenter_id.id,
                'operation_id': operation.id,
                'duration_expected': duration_expected,
                'state': len(workorders) == 0 and 'ready' or 'pending',
                'qty_producing': quantity,
                'capacity': operation.workcenter_id.capacity,
            })
            self.variant_ids.generate_workorder_qc_line(workorder)
            self.generate_workorder_service_line(workorder)
            if workorders:
                workorders[-1].next_work_order_id = workorder.id
            workorders += workorder

            # assign moves; last operation receive all unassigned moves (which case ?)
            moves_raw = self.move_raw_ids.filtered(lambda move: move.operation_id == operation)
            if len(workorders) == len(bom.routing_id.operation_ids):
                moves_raw |= self.move_raw_ids.filtered(lambda move: not move.operation_id)
            moves_finished = self.move_finished_ids.filtered(
                lambda move: move.operation_id == operation)  # TODO: code does nothing, unless maybe by_products?
            moves_raw.mapped('move_line_ids').write({'workorder_id': workorder.id})
            (moves_finished + moves_raw).write({'workorder_id': workorder.id})

        return workorders

    @api.multi
    def generate_workorder_service_line(self, workorder):
        services = self.env['mrp.workorder.service.line']
        done = self.env['mrp.workorder.service.line'].browse()
        for bom in self.bom_id.cmt_service_ids:
            for line in bom.prepare_workorder_service_ids(workorder):
                done += services.create(line)
        return done


class MrpProductionVariant(models.Model):
    _name = 'mrp.production.variant'
    _rec_name = 'product_id'
    _description = 'Line Product Variant'

    production_id = fields.Many2one(comodel_name="mrp.production", string="Variant Order", ondelete="cascade", index=True)
    sequence = fields.Integer('Sequence', default=1)

    product_id = fields.Many2one(comodel_name="product.product", string="Products")
    product_uom_id = fields.Many2one(
        'product.uom', 'Product Unit of Measure', related="product_id.uom_id")
    product_qty = fields.Float('Quantity To Produce', default=1.0, digits=dp.get_precision('Product Unit of Measure'))
    ratio = fields.Float('Ratio', digits=dp.get_precision('Product Unit of Measure'))

    # create mrp.workorder.qc.line
    def generate_workorder_qc_line(self, workorder_id):
        workorders = self.env['mrp.workorder.qc.line']
        done = self.env['mrp.workorder.qc.line'].browse()
        for order in self:
            for line in order.prepare_workorder_qc_line(workorder_id):
                done += workorders.create(line)
        return done

    def prepare_workorder_qc_line(self, workorder_id):
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        template = {
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom_id.id,
            'product_qty': self.product_qty,
            'ratio': self.ratio,
            'workorder_id': workorder_id.id,
            'sequence': self.sequence,
        }
        res.append(template)
        return res






