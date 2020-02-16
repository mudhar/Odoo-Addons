import logging
from datetime import datetime
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.tools import float_round
from odoo.exceptions import UserError, Warning
from odoo.tools import html2plaintext


_logger = logging.getLogger(__name__)


class AssemblyPlan(models.Model):
    _name = 'assembly.plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _date_name = 'date_planned_start'
    _rec_name = 'name'
    _description = 'Assembly Plan'
    _order = 'date_planned_start asc,id'

    @api.model
    def _get_default_picking_type(self):
        return self.env['stock.picking.type'].search([
            ('code', '=', 'mrp_operation'),
            ('warehouse_id.company_id', 'in',
             [self.env.context.get('company_id',
                                   self.env.user.company_id.id), False])],
            limit=1).id

    @api.model
    def get_default_picking_type_po(self):
        return self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('warehouse_id.company_id', 'in',
             [self.env.context.get('company_id',
                                   self.env.user.company_id.id), False])],
            limit=1).id

    @api.model
    def _get_default_location_stock(self):
        return self.env.ref('stock.stock_location_stock').id

    name = fields.Char('Plan Reference', required=True, copy=False, readonly=True, index=True, default='New', track_visibility='always')
    origin = fields.Char(string="Source", copy=False, help="Sumber Dokumen Yang Membuat Dokumen Assembly Plan Ini")
    plan_line_ids = fields.One2many('assembly.plan.line', 'plan_id', string="Variant Plan Lines")
    plan_line_actual_ids = fields.One2many('assembly.plan.line', 'plan_id', string="Variant Actual Lines")

    # Estimasi
    raw_line_ids = fields.One2many('assembly.plan.raw.material', 'plan_id', string="Raw Material Estimasi Lines")
    # Plan
    raw_plan_line_ids = fields.One2many('assembly.plan.raw.material', 'plan_id', string="Raw Material Plan Lines")
    # Actual
    raw_actual_line_ids = fields.One2many('assembly.plan.raw.material', 'plan_id', string="Raw Material Actual Lines")

    cmt_material_line_ids = fields.One2many('assembly.plan.cmt.material', 'plan_id',
                                            string="Aksesoris Plan Lines")
    cmt_material_actual_line_ids = fields.One2many('assembly.plan.cmt.material', 'plan_id', string="Aksesoris On Hand Lines")
    cmt_service_ids = fields.One2many('assembly.plan.services', 'plan_id',
                                      string="Biaya Produksi")
    active = fields.Boolean('Active Plan', default=True, index=True,
                            help="If unchecked, it will allow you to hide the Assembly Production without removing it.")

    product_template_id = fields.Many2one(comodel_name="product.template", string="Product", index=True)
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure')

    # List Data Untuk Buat Record mrp.production
    warehouse_id = fields.Many2one(comodel_name="stock.warehouse", string="Warehouse")
    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type')
    location_id = fields.Many2one(comodel_name="stock.location", string="Raw Materials Location",
                                  default=_get_default_location_stock)
    location_dest_id = fields.Many2one(comodel_name="stock.location", string="Finished Products Location")
    partner_id = fields.Many2one(comodel_name="res.partner", string="CMT Vendor", track_visibility='onchange')
    date_planned_start = fields.Datetime(
        'Scheduled Date Start',
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    date_planned_finished = fields.Datetime(
        'Scheduled Date Finished',
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    purchase_date = fields.Datetime('Purchase Schedule Date',
                                    states={'done': [('readonly', True)],
                                            'cancel': [('readonly', True)]})

    bom_id = fields.Many2one('mrp.bom', 'Bill of Material', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('mrp.production'))
    currency_id = fields.Many2one('res.currency', 'Currency', readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    user_id = fields.Many2one('res.users', string='Responsible', index=True, track_visibility='onchange',
                              default=lambda self: self.env.user)

    mo_ids = fields.One2many(comodel_name="mrp.production", inverse_name="assembly_plan_id",
                             string="Manufacturing Order")
    mo_count = fields.Integer(string="# Plans", compute="_compute_mo_count")
    po_count = fields.Integer(string="#Purchase Orders", compute="_compute_po_count")
    mo_done = fields.Boolean(string="MO Done", compute="_compute_mo_done")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('procurement', 'Procurement'),
        ('on process', 'On Process'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, copy=False, default='draft', track_visibility='always')

    assembly_id = fields.Many2one(comodel_name="assembly.production", string="#Assembly ID", readonly=True,
                                  ondelete='cascade', index=True)

    # Purchase
    # purchase_ids = fields.One2many(comodel_name="purchase.order", inverse_name="assembly_plan_id",
    #                                string="Purchase Orders For Raw Material")
    check_raw_procurement = fields.Boolean(string="Is Raw Material Need Procurement", readonly=True)
    check_cmt_procurement = fields.Boolean(string="Is CMT Material Need Procurement", readonly=True,
                                           )
    show_cmt_consumed = fields.Text(string="List CMT Consumed", compute="_compute_cmt_consume")
    # Kolum Untuk Input Jumlah Quantity Yang Akan Diproduksi
    produce_ids = fields.One2many(comodel_name="assembly.plan.produce", inverse_name="plan_id", string="Produce")
    check_quantity_produce = fields.Boolean(string="Is Quantity Produce Actual Changed?",
                                            compute="_compute_check_quantity_produce")
    # Total Raw Material + Aksesoris + Biaya Produksi
    amount_total = fields.Float(string='Total', compute="_compute_amount_total")
    amount_total_non_service = fields.Float(string='Total Without Service', compute="_compute_amount_total")

    is_locked = fields.Boolean('Is Locked', default=True, copy=False)

    @api.constrains('purchase_date')
    def _check_purchase_date(self):
        self.ensure_one()
        purchase_date = fields.Datetime.from_string(self.purchase_date)
        date_end = fields.Datetime.from_string(self.date_planned_finished)
        date_start = fields.Datetime.from_string(self.date_planned_start)
        if purchase_date and purchase_date > date_end:
            raise UserError(_("Tanggal Purchase Date Tidak Boleh Melebihi Dari Tanggal Selesai Produksi"))
        if purchase_date and purchase_date < date_start:
            raise UserError(_("Tanggal Purchase Date Tidak Boleh Kurang Dari Tanggal Mulai Produksi"))

    @api.onchange('warehouse_id')
    def _onchange_warehouse(self):
        picking_type_id = self.env['stock.picking.type'].search(
            [('code', '=', 'mrp_operation'),
             ('warehouse_id', '=', self.warehouse_id.id)], limit=1)
        if picking_type_id:
            self.update({'location_dest_id': picking_type_id.default_location_src_id.id,
                         'picking_type_id': picking_type_id.id})

    @api.multi
    @api.depends('mo_ids')
    def _compute_mo_done(self):
        for plan in self:
            if plan.mo_ids:
                plan.mo_done = all(mo.state == 'done' for mo in plan.mo_ids) if plan.mo_ids else False

    @api.multi
    @api.depends('produce_ids',
                 'produce_ids.original_quantity_actual')
    def _compute_check_quantity_produce(self):
        for plan in self:
            plan.check_quantity_produce = any(produce.quantity_actual != produce.original_quantity_actual
                                              for produce in plan.produce_ids)

    def _compute_mo_count(self):
        read_group_res = self.env['mrp.production'].read_group([('assembly_plan_id', 'in', self.ids)],
                                                               ['assembly_plan_id'], ['assembly_plan_id'])
        mapped_data = dict([(data['assembly_plan_id'][0], data['assembly_plan_id_count']) for data in read_group_res])
        for assembly in self:
            assembly.mo_count = mapped_data.get(assembly.id, 0)

    def _compute_po_count(self):
        read_group_res = self.env['purchase.order'].read_group([('assembly_plan_id', 'in', self.ids)],
                                                               ['assembly_plan_id'], ['assembly_plan_id'])
        mapped_data = dict([(data['assembly_plan_id'][0], data['assembly_plan_id_count'])
                            for data in read_group_res])
        for assembly in self:
            assembly.po_count = mapped_data.get(assembly.id, 0)

    @api.multi
    @api.depends('raw_line_ids.price_subtotal_actual',
                 'cmt_material_line_ids.price_subtotal_actual',
                 'cmt_service_ids.price_subtotal')
    def _compute_amount_total(self):
        for order in self:
            total_raw = sum(order.raw_line_ids.mapped('price_subtotal_actual'))
            total_cmt = sum(order.cmt_material_line_ids.mapped('price_subtotal_actual'))
            total_service = sum(order.cmt_service_ids.mapped('price_subtotal'))
            order.update({
                'amount_total': total_raw + total_cmt + total_service,
                'amount_total_non_service': total_raw + total_cmt
            })

    @api.multi
    def button_update_quantity(self):
        if self.state == 'draft':
            self._set_quantity_plan()
        if self.state in ['on process', 'procurement']:
            self._set_quantity_actual()

    def _set_quantity_plan(self):
        for produce in self.produce_ids:
            produce.write({'original_quantity_plan': produce.quantity_plan})

            raw_ids = self.raw_line_ids.filtered(
                lambda x: x.attribute_id.id == produce.attribute_id.id)
            for raw in raw_ids:
                raw.write({'qty_to_plan': float_round(
                    raw.product_qty * produce.quantity_plan,
                    precision_rounding=raw.product_id.uom_id.rounding,
                    rounding_method='UP')})

            total_ratio = sum(self.plan_line_ids.filtered(
                lambda x: x.attribute_value_ids[0].id == produce.attribute_id.id
                          or x.attribute_value_ids[1].id == produce.attribute_id.id).mapped('ratio'))
            variant_ids = self.plan_line_ids.filtered(
                lambda x: x.attribute_value_ids[0].id == produce.attribute_id.id
                          or x.attribute_value_ids[1].id == produce.attribute_id.id)
            for variant in variant_ids:
                if variant.product_id:
                    variant.write({'new_qty': float_round((variant.ratio / total_ratio) * produce.quantity_plan,
                                                          precision_rounding=variant.product_uom_id.rounding)})

    def _set_quantity_actual(self):
        for produce in self.produce_ids:
            if produce.attribute_id:
                produce.write({'original_quantity_actual': produce.quantity_actual})
                if produce.quantity_actual == produce.quantity_plan:
                    for line in self.plan_line_ids:
                        if line.actual_quantity != line.new_qty:
                            line.update({'actual_quantity': line.new_qty})

                    raw_ids = self.raw_line_ids.filtered(
                        lambda x: x.attribute_id.id == produce.attribute_id.id)
                    for raw in raw_ids:
                        raw.write({
                            'qty_to_actual': float_round(
                                raw.product_qty * produce.quantity_actual,
                                precision_rounding=raw.product_id.uom_id.rounding,
                                rounding_method='UP')})
                if produce.quantity_actual != produce.quantity_plan:
                    raw_ids = self.raw_line_ids.filtered(
                        lambda x: x.attribute_id.id == produce.attribute_id.id)
                    for raw in raw_ids:
                        raw.write({
                            'qty_to_actual': float_round(
                                raw.product_qty * produce.quantity_actual,
                                precision_rounding=raw.product_id.uom_id.rounding,
                                rounding_method='UP')})

                    total_ratio = sum(self.plan_line_ids.filtered(
                        lambda x: x.attribute_value_ids[0].id == produce.attribute_id.id
                                  or x.attribute_value_ids[1].id == produce.attribute_id.id).mapped('ratio'))
                    variant_ids = self.plan_line_ids.filtered(
                        lambda x: x.attribute_value_ids[0].id == produce.attribute_id.id
                                  or x.attribute_value_ids[1].id == produce.attribute_id.id)
                    for variant in variant_ids:
                        if variant.product_id:
                            variant.write(
                                {'actual_quantity': float_round(
                                    (variant.ratio / total_ratio) * produce.quantity_actual,
                                    precision_rounding=variant.product_uom_id.rounding)})

    @api.multi
    def set_quantity_variant(self):
        if self.state == 'draft':
            for produce in self.produce_ids:
                produce.write({'original_quantity_plan': produce.quantity_plan})

                raw_ids = self.raw_line_ids.filtered(
                    lambda x: x.attribute_id.id == produce.attribute_id.id)
                for raw in raw_ids:
                    raw.write({'qty_to_plan': float_round(
                        raw.product_qty * produce.quantity_plan,
                        precision_rounding=raw.product_id.uom_id.rounding,
                        rounding_method='UP')})

                total_ratio = sum(self.plan_line_ids.filtered(
                    lambda x: x.attribute_value_ids[0].id == produce.attribute_id.id
                              or x.attribute_value_ids[1].id == produce.attribute_id.id).mapped('ratio'))
                variant_ids = self.plan_line_ids.filtered(
                    lambda x: x.attribute_value_ids[0].id == produce.attribute_id.id
                              or x.attribute_value_ids[1].id == produce.attribute_id.id)
                for variant in variant_ids:
                    if variant.product_id:
                        variant.write({'new_qty': float_round((variant.ratio / total_ratio) * produce.quantity_plan,
                                                              precision_rounding=variant.product_uom_id.rounding)})

        if self.state in ['process', 'procurement']:
            for produce in self.produce_ids:
                if produce.attribute_id:
                    produce.write({'original_quantity_actual': produce.quantity_actual})
                    if produce.quantity_actual == produce.quantity_plan:
                        variant_plan_ids = self.mapped('plan_line_ids')
                        self.write({'plan_line_actual_ids': [(6, 0, variant_plan_ids.ids)]})

                        raw_ids = self.raw_line_ids.filtered(
                            lambda x: x.attribute_id.id == produce.attribute_id.id)
                        for raw in raw_ids:
                            raw.write({
                                'qty_to_actual': float_round(
                                    raw.product_qty * produce.quantity_actual,
                                    precision_rounding=raw.product_id.uom_id.rounding,
                                    rounding_method='UP')})
                    if produce.quantity_actual != produce.quantity_plan:
                        raw_ids = self.raw_line_ids.filtered(
                            lambda x: x.attribute_id.id == produce.attribute_id.id)
                        for raw in raw_ids:
                            raw.write({
                                'qty_to_actual': float_round(
                                    raw.product_qty * produce.quantity_actual,
                                    precision_rounding=raw.product_id.uom_id.rounding,
                                    rounding_method='UP')})

                        total_ratio = sum(self.plan_line_ids.filtered(
                            lambda x: x.attribute_value_ids[0].id == produce.attribute_id.id
                                      or x.attribute_value_ids[1].id == produce.attribute_id.id).mapped('ratio'))
                        variant_ids = self.plan_line_ids.filtered(
                            lambda x: x.attribute_value_ids[0].id == produce.attribute_id.id
                                      or x.attribute_value_ids[1].id == produce.attribute_id.id)
                        for variant in variant_ids:
                            if variant.product_id:
                                variant.write(
                                    {'actual_quantity': float_round(
                                        (variant.ratio / total_ratio) * produce.quantity_actual,
                                        precision_rounding=variant.product_uom_id.rounding)})

        return True

    @api.multi
    def _compute_cmt_consume(self):
        cmt_consume_max_than_initial = self.cmt_material_actual_line_ids.filtered(
            lambda x: x.quantity_to_actual > x.qty_available and x.product_id.type == 'product')
        show_consume_text = ''
        if cmt_consume_max_than_initial:
            cmt_consume_text = ''.join('%s: Consumed: %s  On Hand: %s Required: %s \n' %
                                       (cmt.product_id.display_name, cmt.quantity_to_actual, cmt.qty_available,
                                        cmt.quantity_to_actual - cmt.qty_available)
                                       for cmt in cmt_consume_max_than_initial)
            show_consume_text += cmt_consume_text

        raw_consume_max_than_initial = self.raw_actual_line_ids.filtered(
            lambda x: x.qty_to_actual > x.qty_available and x.product_id.type == 'product')
        if raw_consume_max_than_initial:
            raw_consume_text = ''.join('%s: Consumed: %s  On Hand: %s Required: %s \n' %
                                       (raw.product_id.display_name, raw.qty_to_actual, raw.qty_available,
                                        raw.qty_to_actual - raw.qty_available)
                                       for raw in raw_consume_max_than_initial)
            show_consume_text += raw_consume_text
        if show_consume_text:
            self.show_cmt_consumed = html2plaintext(show_consume_text)

    @api.multi
    def compute_check_procurement(self):
        for order in self:
            order.check_raw_procurement = False
            if any(x.need_procurement for x in order.raw_plan_line_ids):
                order.check_raw_procurement = True

            order.check_cmt_procurement = False
            if any(x.need_procurement for x in order.cmt_material_line_ids):
                order.check_cmt_procurement = True

    @api.model
    def create(self, values):
        if values.get('name', _('New')) == _('New') and values.get('partner_id'):
            partner_id = self.env['res.partner'].browse(values.get('partner_id'))
            values['name'] = ''.join('%s/%s' % (partner_id.partner_cmt_code,
                                                self.env['ir.sequence'].next_by_code('assembly.plan'))) or '/'

        plan = super(AssemblyPlan, self).create(values)
        plan.onchange_product_template_id()
        return plan

    @api.multi
    def check_qty_available(self):
        for record in self:
            if record.location_id:
                for stock in record.raw_plan_line_ids:
                    if stock.product_id:
                        qty = record.get_product_availability(record.location_id, stock.product_id)
                        uom_qty = stock.product_id.uom_id._compute_quantity(qty, stock.product_uom_id)
                        stock.update({'qty_available': uom_qty})

                for cmt in record.cmt_material_line_ids:
                    if cmt.product_id:
                        cmt_qty = record.get_product_availability(record.location_id, cmt.product_id)
                        uom_cmt_qty = cmt.product_id.uom_id._compute_quantity(cmt_qty, cmt.product_uom_id)
                        cmt.update({'qty_available': uom_cmt_qty})

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

    @api.multi
    def onchange_product_template_id(self):
        bom_model = self.env['mrp.bom']
        for plan in self:
            if plan.product_template_id:
                plan.bom_id = False
        else:

            bom = bom_model.bom_find_assembly(product_tmpl=plan.product_template_id,
                                              picking_type=plan.picking_type_id,
                                              company_id=plan.company_id.id,
                                              assembly=plan.assembly_id)

            if bom.type == 'normal':
                plan.bom_id = bom.id
            else:
                plan.bom_id = False

            plan.product_uom_id = plan.product_template_id.uom_id.id
            categ_id = plan.product_template_id.uom_id.category_id
            return {'domain': {'product_uom_id': [('category_id', '=', categ_id
                                                   )]}}

    # START FUNGSI FUNGI
    # YANG DIGUNAKAN UNTUK PEMBUATAN RECORD MANUFACTURING ORDER #

    @api.multi
    def get_mo_qty(self):
        for order in self:
            quantity = 0.0
            qty_list = []
            for raw in order.raw_line_ids:
                if raw.product_id.id > 0:
                    qty_list.append(raw.total_actual_quantity)
            quantity += sum(qty_list)
            return quantity

    @api.multi
    def action_create_manufacturing_order(self):
        self.ensure_one()
        for order in self:
            if any([ptype in ['product', 'consu'] for ptype in order.plan_line_ids.mapped('product_id.type')]):
                production_ids = order.mo_ids.filtered(lambda mo: mo.assembly_plan_id and mo.state not in ('done', 'cancel'))
                if not production_ids:
                    # location_src_id = order.picking_type_id.default_location_src_id
                    # location_dest_id = order.picking_type_id.default_location_dest_id
                    res = {
                        'partner_id': order.partner_id.id,
                        'product_template_id': order.product_template_id.id,
                        'product_uom_id': order.product_uom_id.id,
                        'product_qty': sum(order.produce_ids.mapped('quantity_actual')),
                        'bom_id': order.bom_id.id,
                        'picking_type_id': order.picking_type_id.id,
                        'company_id': order.company_id.id,
                        'date_planned_start': order.date_planned_start,
                        'date_planned_finished': order.date_planned_finished,
                        'location_src_id': order.location_id.id,
                        'location_dest_id': order.location_dest_id.id,
                        'assembly_plan_id': order.id,
                        'origin': order.name,
                    }
                    production_id = self.env['mrp.production'].create(res)
                else:
                    production_id = production_ids[0]
                order.plan_line_ids.generate_production_variant(production_id)
                # order.assign_production_finished_picking()

        return True

    @api.multi
    def assign_production_finished_picking(self):
        for order in self:
            production_ids = order.mo_ids.filtered(lambda mo: mo.assembly_plan_id and mo.state == 'confirmed')
            if production_ids:
                production_ids._generate_finished_picking()
            return True

    @api.multi
    def check_remaining_qty(self):
        self.ensure_one()
        for order in self:
            for produce in order.produce_ids:
                if produce.attribute_id:
                    total_produce_plan = sum(order.plan_line_ids.filtered(
                        lambda x: x.attribute_value_ids[0].id == produce.attribute_id.id
                                  or x.attribute_value_ids[1].id == produce.attribute_id.id).mapped('new_qty'))
                    if total_produce_plan and total_produce_plan != produce.quantity_plan:
                        message = _("Total Quantity Untuk Warna %s %s Pcs(s) Pada Tabel Variant Plan"
                                    "\n"
                                    "\n Tidak Sama Dengan Total Quantity Yang Akan Diproduksi %s Pcs(s)"
                                    "\n Pada Tabel Plan Quantity To Produce Untuk Warna %s"
                                    "\n Samakan Total Quantity Pada Tabel Variant Plan Dengan Tabel To Produce") % (
                                      produce.attribute_id.name, total_produce_plan,
                                      produce.quantity_plan, produce.attribute_id.name)
                        raise UserError(message)

                    total_produce_actual = sum(
                        order.plan_line_ids.filtered(lambda x: x.attribute_value_ids[0].id == produce.attribute_id.id
                                                               or x.attribute_value_ids[1].id == produce.attribute_id.id).mapped('actual_quantity'))
                    if total_produce_actual and total_produce_actual != produce.quantity_actual:
                        message = _("Total Quantity Untuk Warna %s %s Pcs(s) Pada Kolum Variant On Hand"
                                    "\n"
                                    "\n Tidak Sama Dengan Total Quantity Yang Akan Diproduksi %s Pcs(s)"
                                    "\n Pada Kolum Actual Quantity To Produce Untuk Warna %s"
                                    "\n Samakan Total Quantity Pada Kolom Variant On Hand Dengan Kolom Produce") % (
                                      produce.attribute_id.name, total_produce_actual,
                                      produce.quantity_actual, produce.attribute_id.name)

                        raise UserError(message)

        return True

    @api.multi
    def copy(self, default=None):
        default = dict(default or {})
        self.ensure_one()
        default.update({
            'state': 'draft',
            'name': self._get_default_name(),
        })
        return super(AssemblyPlan, self).copy(default)

    @api.multi
    def unlink(self):
        for order in self:
            if order.state not in ('draft', 'cancel'):
                raise UserError(_('Assembly Plan Perlu Di Cancel Dulu Baru Bisa Dihapus'))

        return super(AssemblyPlan, self).unlink()

    @api.multi
    def button_to_approve(self):
        for record in self:
            if not record.partner_id:
                raise UserError(_("Pilih Vendor CMT Terlebih Dahulu"))
            for produce in record.produce_ids:
                if not produce.quantity_plan:
                    raise UserError(_("Isi Kolum PLAN Quantity To Produce."
                                      "\n Pada Tabel Produce Terlebih Dahulu"))
                if produce.quantity_plan != produce.original_quantity_plan:
                    raise UserError(_("Anda Baru Melakukan Perubahan Plan Quantity To Produce"
                                      "\n Klik Tombol Update Untuk Memperbaharuinya"))
            consume_qty_plan = sum(record.raw_line_ids.mapped('qty_to_plan'))
            if not consume_qty_plan and record.state == 'draft':
                raise UserError(_("Kolom Plan Expected Consume Qty Belum Terisi"
                                  "\n Klik Tombol Update Pada Tabel To Produce Untuk Mengisinya"))

            consume_qty_actual = sum(record.raw_line_ids.mapped('qty_to_actual'))
            if not consume_qty_actual and record.state in ['procurement', 'process']:
                raise UserError(_("Kolom Actual Expected Consume Qty Belum Terisi"
                                  "\n Klik Tombol Update Pada Tabel To Produce Untuk Mengisinya"))

            record.check_remaining_qty()
            record.check_qty_available()
            # record.check_warning_stock()
            record.compute_check_procurement()

            record.write({'state': 'on process'})
        return True

    @api.multi
    def button_done(self):
        for order in self:
            if order.check_quantity_produce:
                raise UserError(_("Anda Melakukan Perubahan Jumlah Quantity Actual Pada Koloum Produce"
                                  "\n Harap Update Dulu Jumlah Quantity Pada Kolom Variant On Hand"
                                  "\n Dengan Memencet Tombol Update Finish Goods"))
            for produce in order.produce_ids:
                if not produce.quantity_actual:
                    raise UserError(_("Isi Actual Quantity To Produce Pada Produce Terlebih Dahulu."
                                      "\n"
                                      "**Kolum Actual Quantity To Produce = Berapa Pcs Produk Yang Jadi Diproduksi"))

            for record in order.plan_line_ids:
                if not (record.new_qty and record.actual_quantity):
                    raise UserError(_("Kolum Variants Plan dan Variants On Hand Belum Terisi, "
                                      "Klik Tombol Update QTY Agar qty Pada Kolum Tsb Terisi"))
            order.check_remaining_qty()
            raw_final = sum(order.produce_ids.mapped('quantity_actual'))

            if order.show_cmt_consumed:
                raise UserError(_("Anda Berencana Memproduksi Sejumlah %s"
                                  "\n Sedangkan Jumlah Yang Dikonsumsi Pada CMT Tidak Mencukupi Dengan STOCk yang Ada"
                                  "\n Anda Perlu Membuat Procurement Untuk Stock CMT Yang Tidak Mencukupi"
                                  "\n"
                                  "\n Berikut List CMT Yang Tidak Mencukupi Untuk Jumlah Produksi Yang Anda Buat:"
                                  "\n"
                                  "\n %s")
                                % (raw_final, order.show_cmt_consumed))
            order._update_assembly_price_unit()
            order.write({'state': 'done'})
            order.update_bom_line()
            order.action_create_manufacturing_order()

        return True

    @api.multi
    def _update_assembly_price_unit(self):
        """
        Update Assembly Design Unit Price Untuk Raw Material, Accessories, Services.
        :return: True
        """
        for plan in self:
            assembly_id = plan.assembly_id
            assembly_material_ids = self.env['assembly.raw.material.line'].search(
                [('assembly_id', '=', assembly_id.id)])
            if assembly_material_ids:
                for raw in plan.raw_actual_line_ids:
                    for assembly_raw in assembly_material_ids.filtered(
                            lambda x: x.product_id.id == raw.product_id.id):
                        assembly_raw.write({'price_unit': raw.price_unit})
            assembly_service_ids = self.env['assembly.cmt.product.service'].search(
                [('assembly_id', '=', assembly_id.id)])
            if assembly_service_ids:
                for service in plan.cmt_service_ids:
                    for assembly_service in assembly_service_ids.filtered(
                            lambda x: x.product_id.id == service.product_id.id):
                        assembly_service.write({'price_unit': service.price_unit})
            assembly_accessories_ids = self.env['assembly.cmt.material.line'].search(
                [('assembly_id', '=', assembly_id.id)])
            if assembly_accessories_ids:
                for accessories in plan.cmt_material_actual_line_ids:
                    for assembly_accessories in assembly_accessories_ids.filtered(
                            lambda x: x.product_id.id == accessories.product_id.id):
                        assembly_accessories.write({'price_unit': accessories.price_unit,
                                                    })

        return True

    @api.multi
    def button_cancel(self):
        if any(production.state != 'cancel' for production in self.mapped('mo_ids')):
            raise UserError(_("Anda Tidak Dapat Membatalkan Assembly Plan."
                              "\n Manufacturing Order Harus Dibatalkan Terlebih Dahulu"))
        self._action_cancel()
        return True

    # Informasi Apabila Membatalkan Dokumen Assembly Plan Ini
    @api.multi
    def _action_cancel(self):
        # cek po yang terbentuk jika masih di draft, confirmed
        po_ids = self.env['purchase.order'].search([('assembly_plan_id', '=', self.id)])

        if any(po.state not in ['done', 'purchase', 'cancel'] for po in po_ids):
            message = _('\t\tApakah Anda Yakin Membatalkan Dokumen Ini ? \n'
                        '\t\tAda Purchase Order Yang Terbentuk Dari Dokumen Ini Sedang Dalam Proses\n'
                        '\t\tBatalkan Terlebih Dahulu Purchase Order Tsb Baru Anda Bisa Membatalkan Dokumen Ini')
            raise Warning(_(message))
        else:
            self.action_cancel()
            self.assembly_id.action_cancel()
            self.bom_id.sudo().write({'active': False})

        return True

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True

    @api.multi
    def update_bom_line(self):
        for order in self:

            bom_lines = order.bom_id.mapped('bom_line_ids')
            for line in bom_lines:
                for raw in order.raw_line_ids:
                    if raw.product_id.id != line.product_id.id:
                        continue

                    if raw.product_id.id == line.product_id.id:
                        line.write({'product_qty': raw.qty_to_actual})

                for cmt in order.cmt_material_line_ids:
                    if cmt.product_id.id != line.product_id.id:
                        continue

                    if cmt.product_id.id == line.product_id.id:
                        line.write({'product_qty': cmt.quantity_to_actual,
                                    })
        return True

    # Create Purchase Order #
    @api.multi
    def action_create_purchase_order(self):
        self.ensure_one()

        orders_to_procurement = self.filtered(lambda x: x.check_raw_procurement or x.check_cmt_procurement
                                                        and x.state == 'on process')
        for order in orders_to_procurement:
            if not order.purchase_date:
                raise UserError(_("Silahkan Dipilih Tanggal Purchase Date Terlebih Dahulu\n"))
            if order.check_raw_procurement:
                for raw_line in order.raw_line_ids.filtered(lambda x: x.product_id and x.need_procurement):
                    order.create_purchase_order(raw_line)
                    order.write({'check_raw_procurement': False})
            if order.check_cmt_procurement:
                for cmt_line in order.cmt_material_line_ids.filtered(lambda x: x.product_id and x.need_procurement):
                    order.create_purchase_order(cmt_line)
                    order.write({'check_cmt_procurement': False})
        return orders_to_procurement.write({'state': 'procurement'})

    @api.model
    def _prepare_purchase_order(self, partner_id, picking_type_id):
        return {
            'name': 'New',
            'state': 'draft',
            'assembly_plan_id': self.id,
            'partner_id': partner_id.id,
            'picking_type_id': picking_type_id,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'date_order': datetime.today(),
            'date_planned': self.purchase_date,
            'origin': self.name,
            'product_select_type': 'materials',
        }

    @api.model
    def _prepare_purchase_order_line(self, po, product_id, product_qty, product_uom_id, price_unit, partner_id):
        procurement_uom_po_qty = product_uom_id._compute_quantity(product_qty, product_id.uom_po_id)
        procurement_uom_po_price = product_uom_id._compute_price(price_unit, product_id.uom_po_id)
        product_lang = product_id.with_context({
            'lang': partner_id.lang,
            'partner_id': partner_id.id,
        })
        uom_po_id = product_id.uom_po_id.id
        name = product_lang.display_name
        taxes = product_id.supplier_taxes_id
        fpos = po.fiscal_position_id
        taxes_id = fpos.map_tax(taxes) if fpos else taxes
        if taxes_id:
            taxes_id = taxes_id.filtered(lambda x: x.company_id.id == self.company_id.id)

        return {
            'name': name,
            'product_qty': procurement_uom_po_qty,
            'product_id': product_id.id,
            'product_uom': uom_po_id,
            'price_unit': procurement_uom_po_price,
            'date_planned': self.purchase_date,
            'order_id': po.id,
            'taxes_id': [(6, 0, taxes_id.ids)],
        }

    @api.model
    def _make_po_get_domain(self, partner_id, picking_type_id):
        domain = (
            ('state', '=', 'draft'),
            ('picking_type_id', '=', picking_type_id),
            ('company_id', '=', self.company_id.id),
            ('assembly_plan_id', '=', self.id),
            ('partner_id', '=', partner_id.id),
        )
        return domain

    @api.multi
    def create_purchase_order(self, line):
        purchase_order_model = self.env['purchase.order']
        purchase_order_line_model = self.env['purchase.order.line']
        picking_type_id = self.get_default_picking_type_po()
        cache = {}
        po = self.env['purchase.order']
        if line.product_id and line.need_procurement:
            if not line.product_id.seller_ids:
                raise UserError(_("Product %s Tidak Ada Vendor Yang Diinput") % line.product_id.display_name)
            partner_id = line.product_id.seller_ids[0].mapped('name')

            domain = self._make_po_get_domain(partner_id, picking_type_id)
            if domain in cache:
                po = cache[domain]
            elif domain:
                po = self.env['purchase.order'].search([dom for dom in domain])
                po = po[0] if po else False
                cache[domain] = po
            if not po:
                purchase_data = self._prepare_purchase_order(partner_id, picking_type_id)
                po = purchase_order_model.create(purchase_data)
                cache[domain] = po

            # Create Line
            product_qty = line.qty_to_plan - line.qty_available
            purchase_line_data = self._prepare_purchase_order_line(
                po, line.product_id, product_qty, line.product_uom_id, line.price_unit, partner_id)
            purchase_order_line_model.create(purchase_line_data)























