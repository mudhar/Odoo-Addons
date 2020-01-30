import logging
from datetime import datetime
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_round, float_compare

_logger = logging.getLogger(__name__)


class MrpWorkOrder(models.Model):
    _inherit = 'mrp.workorder'
    _order = 'production_id,sequence'

    @api.one
    @api.depends('next_work_order_id',
                 'is_cutting',
                 'qc_ids',
                 'qc_ids.qty_produced',
                 'qc_ids.product_qty',
                 'qc_ids.is_updated_from_prev_workorder')
    def compute_total_qc_produced(self):
        if self.next_work_order_id and self.is_cutting:
            qc_produced = sum(self.qc_ids.mapped('qty_produced'))
            self.tot_qc_qty_produced = qc_produced

            qc_producing = sum(self.qc_ids.mapped('product_qty'))
            self.qc_qty_remaining = qc_producing - self.tot_qc_qty_produced
        if self.next_work_order_id and not self.is_cutting:
            qc_produced = sum(self.qc_ids.mapped('qty_produced'))
            self.tot_qc_qty_produced = qc_produced

            qc_producing = sum(self.qc_ids.filtered(lambda x: x.is_updated_from_prev_workorder).mapped('product_qty'))
            self.qc_qty_remaining = qc_producing - self.tot_qc_qty_produced

        if not self.next_work_order_id and not self.is_cutting:
            qc_produced = sum(self.qc_ids.mapped('qty_produced'))
            self.tot_qc_qty_produced = qc_produced

            qc_producing = sum(self.qc_ids.filtered(lambda x: x.is_updated_from_prev_workorder).mapped('product_qty'))
            self.qc_qty_remaining = qc_producing - self.tot_qc_qty_produced

        return True

    product_template_id = fields.Many2one(
        'product.template', 'Product To Produce',
        related='production_id.product_template_id', readonly=True,
        help='Technical: used in views only.', store=True)
    sequence = fields.Integer(string='Sequence', default=100)

    backdate_start = fields.Datetime(
        'Effective Start Date',
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    backdate_finished = fields.Datetime(
        'Effective End Date',
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})

    partner_id = fields.Many2one(comodel_name="res.partner", string="CMT Vendor")
    qc_ids = fields.One2many(comodel_name="mrp.workorder.qc.line", inverse_name="workorder_id", string="QC Lines")
    product_service_ids = fields.One2many(comodel_name="mrp.workorder.service.line", inverse_name="work_order_id",
                                          string="Service Lines")

    additional_quantity = fields.Float(string="Additional Quantity", digits=dp.get_precision('Product Unit of Measure'))
    # qc_final = fields.Float(string="Quantity Final", digits=dp.get_precision('Product Unit of Measure'),
    #                         compute="compute_qty_final")

    is_change_vendor = fields.Boolean(string="changed vendor", readonly=True)
    is_cutting = fields.Boolean(string="Cutting")
    check_qc_to_done = fields.Boolean(string="Check Qc To Done", compute="compute_check_qc_to_done")
    check_assembly_plan_id = fields.Boolean(string="Check Assembly Plan",
                                            help="Teknikal View Untuk Menghilang Field Tertentu "
                                                 "Apabila MO Dibuat Dari Assembly Plan", compute="_get_assembly_plan")
    product_tracking_template = fields.Selection(
        'Product Tracking', related='production_id.product_template_id.tracking',
        help='Technical: used in views only.')

    qc_qty_remaining = fields.Float(string="Sisa Total Input", digits=dp.get_precision('Product Unit of Measure'),
                                    help="Teknikal View Untuk Mengecek Apakah Input Hasil Masih Bisa Ditambahkan",
                                    compute="compute_total_qc_produced")
    qc_done = fields.Float(string="Qc Done", digits=dp.get_precision('Product Unit of Measure'))
    tot_qc_qty_produced = fields.Float(string="Total QC Qty Produced", digits=dp.get_precision('Product Unit of Measure'),
                                       compute="compute_total_qc_produced")

    po_count = fields.Integer(string="#PO", compute="_compute_po_count")
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency", required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.user.company_id.id)
    po_ids = fields.One2many(comodel_name="purchase.order", inverse_name="work_order_id", string="#Of PO")
    # price_paid = fields.Float(string="Total Paid", digits=dp.get_precision('Product Price'),
    #                               compute="_compute_price_paid", default=0.0)
    purchase_created = fields.Boolean(string="Purchase Created")

    # Tambah State Waiting Approval
    state = fields.Selection(selection_add=[('waiting', 'Waiting Approval New Work Order'),
                                            ('approve', 'Request For New Work Order Approved'),
                                            ('reject', 'Request For New Work Order Rejected'),
                                            ('waiting skip', 'Waiting Approval Skip Process'),
                                            ('approve skip', 'Request For Skip Process Approved'),
                                            ('reject skip', 'Request For Skip Process Rejected')])
    workorder_created = fields.Boolean(string="Workorder Created By Wizard")
    skipped = fields.Boolean(string="Skipped")
    # Hanya Untuk Teknikal View
    service_categ_id = fields.Many2one(comodel_name="product.category", string="Set Service Category",
                                       default=lambda self: self.env.user.company_id.service_categ_id.id)
    location_reject_id = fields.Many2one(comodel_name="stock.location", string="Stock Location Reject",
                                         default=lambda self: self.env.user.company_id.location_reject_id.id)

    check_move_created = fields.Boolean(string="Check All Move Created", compute="_compute_move_created",
                                        help="Teknikal View Untuk Mengecek Stock Move Sudah Kebentuk Semua")

    prev_wo_done = fields.Boolean(string="Check Prev Work Order State", compute="_compute_prev_wo_done")
    is_locked = fields.Boolean('Is Locked', default=True, copy=False)
    purchase_visible = fields.Boolean(string='Visible button purchase', compute="_compute_button_purchase")
    produced_less_than_planned = fields.Boolean(string="Check Quantity Input less Than Planned",
                                                compute="_compute_produced_less_than_panned")
    is_work_order_finish = fields.Boolean(compute="_compute_is_work_order_finish")

    @api.multi
    @api.depends('check_qc_to_done',
                 'state')
    def _compute_button_purchase(self):
        for work_order in self:
            work_order.purchase_visible = work_order.check_qc_to_done and \
                                          work_order.state not in ('done', 'cancel')

    @api.multi
    @api.depends('next_work_order_id', 'is_cutting')
    def _compute_is_work_order_finish(self):
        for work_order in self:
            work_order.is_work_order_finish = (not work_order.next_work_order_id and not work_order.is_cutting)

    @api.depends('qc_qty_remaining')
    def _compute_produced_less_than_panned(self):
        for work_order in self:
            work_order.produced_less_than_planned = float_compare(
                work_order.qc_done, work_order.qty_producing,
                precision_rounding=work_order.product_uom_id.rounding) == -1

    @api.multi
    @api.depends('next_work_order_id', 'is_cutting')
    def _compute_prev_wo_done(self):
        for work_order in self:
            if work_order.next_work_order_id and work_order.is_cutting:
                return False
            elif work_order.next_work_order_id and not work_order.is_cutting:
                prev_wo_done = self.env['mrp.workorder'].search(
                    [('production_id', '=', work_order.production_id.id)
                     ]).filtered(lambda x: x.sequence < work_order.sequence)
                work_order.prev_wo_done = all(prev_wo.state == 'done'
                                              for prev_wo in prev_wo_done) if prev_wo_done else False
            elif not work_order.next_work_order_id and not work_order.is_cutting:
                return False
        return True

    @api.depends('next_work_order_id',
                 'is_cutting',
                 'qc_ids',
                 'qc_ids.qc_finished_ids',
                 'qc_ids.qc_finished_ids.stock_move_created')
    def _compute_move_created(self):
        for work_order in self:
            if not work_order.next_work_order_id and not work_order.is_cutting:
                qc_done = all(qc.state == 'done' for qc in work_order.qc_ids) if work_order.qc_ids else False
                stock_move_created = all(line.stock_move_created
                                         for line in work_order.qc_ids.mapped('qc_finished_ids')
                                         ) if work_order.qc_ids.mapped('qc_finished_ids') else False
                work_order.check_move_created = qc_done and stock_move_created

    def _compute_po_count(self):
        read_group_res = self.env['purchase.order'].read_group([('work_order_id', 'in', self.ids)], ['work_order_id'],
                                                               ['work_order_id'])
        mapped_data = dict([(data['work_order_id'][0], data['work_order_id_count']) for data in read_group_res])
        for record in self:
            record.po_count = mapped_data.get(record.id, 0)

    @api.multi
    @api.depends('production_id.assembly_plan_id')
    def _get_assembly_plan(self):
        for order in self:
            if order.production_id and order.production_id.assembly_plan_id:
                order.check_assembly_plan_id = True
            else:
                order.check_assembly_plan_id = False
        return True

    @api.multi
    @api.depends('qc_ids.state')
    def compute_check_qc_to_done(self):
        for work_order in self:
            work_order.check_qc_to_done = all(line.state == 'done'
                                              for line in work_order.qc_ids) if work_order.qc_ids else False

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            if record.check_assembly_plan_id and record.product_template_id:
                res.append((record['id'], "%s - %s - %s" % (record.production_id.name, record.product_template_id.name, record.name)))
            elif not record.check_assembly_plan_id and record.product_id:
                res.append((record['id'], "%s - %s - %s" % (record.production_id.name, record.product_id.name, record.name)))
        return res

    @api.multi
    def button_start(self):
        self.ensure_one()
        res = super(MrpWorkOrder, self).button_start()

        if self.check_assembly_plan_id and res:
            if not self.backdate_start:
                raise UserError(_("Input Tanggal Mulai Proses %s") % self.name)
            self.write({'date_start': self.backdate_start,
                        'date_planned_start': self.backdate_start})
            if self.time_ids and self.mapped('time_ids').filtered(
                    lambda wo: wo.workorder_id and wo.date_start != self.backdate_start):
                self.mapped('time_ids').write({'date_start': self.backdate_start})

            if self.production_id.date_start != self.backdate_start:
                self.production_id.write({'date_start': self.backdate_start})

            if self.next_work_order_id and self.is_cutting:
                return True

            if self.next_work_order_id and not self.is_cutting:
                for work_order in self.env['mrp.workorder'].search([('production_id', '=', self.production_id.id)]):
                    if any(work.state != 'done' for work in work_order.filtered(lambda x: x.is_cutting)):
                        raise UserError(_("Work Order Cutting belum Done"))

            if not self.next_work_order_id and not self.is_cutting:
                for work_order in self.env['mrp.workorder'].search([('production_id', '=', self.production_id.id)]):
                    if any(work.state != 'done' for work in work_order.filtered(lambda x: x.is_cutting)):
                        raise UserError(_("Work Order belum Done"))
        return res

    @api.multi
    def button_finish(self):
        self.ensure_one()
        result = super(MrpWorkOrder, self).button_finish()
        if not self.backdate_finished:
            raise UserError(_("Input Tanggal Selesai Process %s") % self.name)
        if self.backdate_finished and result:
            self.write({'date_finished': self.backdate_finished})
        return result

    @api.multi
    @api.depends('qty_production', 'qty_produced')
    def _compute_qty_remaining(self):
        for wo in self:
            if wo.check_assembly_plan_id:
                if not wo.additional_quantity:
                    wo.qty_remaining = float_round(wo.qty_production - wo.qty_produced,
                                                   precision_rounding=wo.production_id.product_uom_id.rounding)
            else:
                return super(MrpWorkOrder, self)._compute_qty_remaining()

    @api.multi
    def record_production(self):
        for production in self:
            if production.check_assembly_plan_id:
                return production.record_production_assembly()
            else:
                return super(MrpWorkOrder, self).record_production()

    @api.multi
    def record_production_assembly(self):
        self.ensure_one()
        if not self.purchase_created:
            return self.button_show_message_warning()
        else:
            return self._set_record_production()

    @api.multi
    def _set_record_production(self):
        for work_order in self:
            if work_order.qty_producing <= 0:
                raise UserError(
                    _('Please set the quantity you are currently producing. It should be different from zero.'))

            if not work_order.check_qc_to_done:
                raise UserError(_('Anda Belum Melakukan Input Hasil Atau Kolom Input Hasil Statusnya Belum Done'))

                # One a piece is produced, you can launch the next work order
            if work_order.next_work_order_id.state == 'pending':
                work_order.next_work_order_id.state = 'ready'

                # self.qty_produced += self.qty_producing

                # self.check_sisa_qty_qc()

            if work_order.next_work_order_id and work_order.is_cutting:
                work_order.qty_produced += float_round(work_order.qc_done,
                                                       precision_rounding=work_order.production_id.product_uom_id.rounding)

                work_order.update_product_variant_quantity()

                work_order.next_work_order_id.write(
                    {'additional_quantity': float_round(work_order.qc_done,
                                                        precision_rounding=work_order.production_id.product_uom_id.rounding),
                     'qty_producing': float_round(work_order.qc_done,
                                                  precision_rounding=work_order.production_id.product_uom_id.rounding)
                     })

                # self.action_update_plan_workorder()

            if work_order.next_work_order_id and not work_order.is_cutting:
                qc_updated = work_order.qc_ids.filtered(lambda x: x.is_updated_from_prev_workorder)
                # qc_not_updated = self.qc_ids.filtered(lambda x: not x.is_updated_from_prev_workorder)
                if len(qc_updated) != len(work_order.qc_ids):
                    raise UserError(_("Anda Tidak Bisa Menyelesaikan Pekerjaan"
                                      "\n Karena Work Order Sebelumnya Masih Dalam Proses"))
                work_order.qty_produced += float_round(work_order.qc_done,
                                                       precision_rounding=work_order.production_id.product_uom_id.rounding)
                work_order.next_work_order_id.write(
                    {'additional_quantity': float_round(work_order.qc_done,
                                                        precision_rounding=work_order.production_id.product_uom_id.rounding),
                     'qty_producing': float_round(work_order.qc_done,
                                                  precision_rounding=work_order.production_id.product_uom_id.rounding)
                     })
                # self.action_update_plan_workorder()

            if not work_order.next_work_order_id and not work_order.is_cutting:
                qc_updated = work_order.qc_ids.filtered(lambda x: x.is_updated_from_prev_workorder)
                # qc_not_updated = self.qc_ids.filtered(lambda x: not x.is_updated_from_prev_workorder)
                if len(qc_updated) != len(work_order.qc_ids):
                    raise UserError(_("Anda Tidak Bisa Menyelesaikan Pekerjaan"
                                      "\n Karena Work Order Sebelumnya Masih Dalam Proses"))
                work_order.qty_produced += float_round(work_order.qc_done,
                                                       precision_rounding=work_order.production_id.product_uom_id.rounding)
                # self.action_update_plan_workorder()
                # self.action_update_plan_sample()
                if all(not qc_move.stock_move_created for qc_move in work_order.qc_ids.mapped('qc_finished_ids')):
                    raise UserError(_("Semua Inputan Belum Dibuat STBJ"
                                      "\n Klik Tombol Receive Good Terlebih Dahulu"))

            work_order.button_finish()

            return True

    # Update Product Quantity Pada Work Order Berikutnya
    @api.multi
    def update_product_variant_quantity(self):

        for variant in self.qc_ids.filtered(lambda x: x.state == 'done' and x.qc_good):
            products = self.next_work_order_id.qc_ids.filtered(
                lambda x: (x.product_id.id == variant.product_id.id) and (x.state not in ('done', 'cancel')))
            products.write({'product_qty': variant.qc_good,
                            'is_updated_from_prev_workorder': True})

        return True

    # button invoice
    @api.multi
    def button_procurement(self):
        self.ensure_one()
        return {
            'name': _('Create Purchase Order'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'vendor.invoice.wizard',
            'view_id': self.env.ref('textile_assembly.vendor_invoice_wizard_view_form').id,
            'type': 'ir.actions.act_window',
            'context': {
                'product_ids': self.product_service_ids.filtered(
                    lambda x: not x.has_po).mapped('product_id').ids},
            'target': 'new',
        }

    def action_toggle_is_locked(self):
        self.ensure_one()
        self.is_locked = not self.is_locked
        return True

    @api.multi
    def button_show_message_warning(self):
        self.ensure_one()
        return {
            'name': _('Warning Purchase Not Created'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase_created_message.wizard',
            'view_id': self.env.ref('textile_assembly.purchase_message_created_wizard_view_form').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def button_new_workorder(self):
        self.ensure_one()
        if not self.service_categ_id:
            raise UserError(_("Parent Product Service Category Not Found"))

        if any(order.state in ['waiting', 'reject'] for order in self.qc_ids):
            raise UserError(_("Ada Salah Satu Inputan Hasil Statusnya Dalam Waiting Atau Reject"
                              "\n Inputan Hasil Statusnya Harus Dalam Done"
                              "\n Bila Sudah Dilakukan Input"))
        workorders = self.env['mrp.workorder'].search(
            [('production_id', '=', self.production_id.id)]).filtered(lambda x: x.workcenter_id).mapped('workcenter_id')
        products = self.env['product.product'].search(
            [('categ_id.parent_id', '=', self.service_categ_id.id),
             ('type', '=', 'service')])
        # product_ids = self.product_service_ids.filtered(
        #     lambda x: x.product_id.id not in products.ids).mapped('product_id')
        product_ids = []
        service_ids = self.product_service_ids.mapped('product_id').ids
        for product in products:
            if product.id and product.id not in service_ids:
                product_ids.append(product.id)

        workcenters = self.env['mrp.workcenter'].search([('id', 'not in', workorders.ids)])

        return {
            'name': _('New Work Order'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'workorder.extension.wizard',
            'view_id': self.env.ref('textile_assembly.workorder_extension_wizard_view_form').id,
            'type': 'ir.actions.act_window',
            'context': {
                'workcenter_ids': workcenters.ids,
                'product_ids': product_ids
            },
            'target': 'new',
        }

    @api.multi
    def set_product_service_category(self):
        company = self.env['res.company'].sudo()
        category_id = company.browse(self.company_id.id).mapped('service_categ_id')
        if not category_id:
            raise UserError(_("Parent Product Service Category Not Found"))
        self.update({'service_categ_id': category_id.id})

    @api.multi
    def button_add_product_service(self):
        self.ensure_one()
        if not self.service_categ_id:
            self.set_product_service_category()

        products = self.env['product.product'].search(
            [('categ_id.parent_id', '=', self.service_categ_id.id),
             ('type', '=', 'service')])

        product_ids = []
        service_ids = self.product_service_ids.mapped('product_id').ids
        for product in products:
            if product.id and product.id not in service_ids:
                product_ids.append(product.id)

        return {
            'name': _('New Product Service'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp_workorder.product_service.wizard',
            'view_id': self.env.ref('textile_assembly.product_service_wizard_view_form').id,
            'type': 'ir.actions.act_window',
            'context': {
                'product_ids': product_ids,
            },
            'target': 'new',
        }

    @api.multi
    def button_remove_product_service(self):
        self.ensure_one()
        product_ids = []
        work_order_ids = self.env['mrp.workorder'].search([('production_id', '=', self.production_id.id)])
        if work_order_ids:
            product_service_ids = work_order_ids.mapped('product_service_ids').filtered(
                lambda x: not x.has_po).mapped('product_id')
            for product in product_service_ids:
                product_ids.append(product.id)

        return {
            'name': _('Remove Product Service'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp_workorder.product_service_remove.wizard',
            'view_id': self.env.ref('textile_assembly.product_service_remove_wizard_view_form').id,
            'type': 'ir.actions.act_window',
            'context': {
                'product_ids': product_ids,
            },
            'target': 'new',
        }


    @api.multi
    def button_request_new_workorder(self):
        self.write({'state': 'waiting'})
        return True

    @api.multi
    def button_request_reject(self):
        self.write({'state': 'reject'})
        return True

    @api.multi
    def button_approve_new_workorder(self):
        self.write({'state': 'approve'})
        return True

    @api.multi
    def button_skip(self):
        self.write({'state': 'waiting skip'})
        return True

    @api.multi
    def button_reject_skip_process(self):
        self.write({'state': 'reject skip'})
        return True

    @api.multi
    def button_approve_skip_process(self):
        self.write({'state': 'approve skip'})
        return True

    @api.multi
    def skip_work_order(self):
        if self.next_work_order_id.state == 'pending':
            self.next_work_order_id.state = 'ready'

        if self.next_work_order_id and not self.is_cutting:
            qc_updated = self.qc_ids.filtered(lambda x: x.is_updated_from_prev_workorder)
            # qc_not_updated = self.qc_ids.filtered(lambda x: not x.is_updated_from_prev_workorder)
            if len(qc_updated) != len(self.qc_ids):
                raise UserError(_("Anda Tidak Bisa Menyelesaikan Pekerjaan"
                                  "\n Karena Work Order Sebelumnya Masih Dalam Proses"))
            quantity_initial = sum(
                self.qc_ids.filtered(lambda x: x.is_updated_from_prev_workorder).mapped('product_qty'))

            for variant in self.qc_ids.filtered(lambda x: x.product_qty):
                products = self.next_work_order_id.qc_ids.filtered(
                    lambda x: (x.product_id.id == variant.product_id.id) and (x.state != 'done'))
                products.write({'product_qty': variant.product_qty,
                                'is_updated_from_prev_workorder': True})

            self.qc_ids.write({'state': 'done'})

            self.qty_produced += float_round(quantity_initial,
                                             precision_rounding=self.production_id.product_uom_id.rounding)
            self.next_work_order_id.write(
                {'additional_quantity': float_round(quantity_initial,
                                                    precision_rounding=self.production_id.product_uom_id.rounding),
                 'qty_producing': float_round(quantity_initial,
                                              precision_rounding=self.production_id.product_uom_id.rounding)
                 })
            self.skipped = True
            self.button_finish()

        return True

    @api.multi
    def set_location_reject_id(self):
        company = self.env['res.company']
        location_reject_id = company.browse(self.company_id.id).mapped('location_reject_id')
        if not location_reject_id:
            raise UserError(_("Stock Location Reject Not Found"))

        self.update({'location_reject_id': location_reject_id.id})

    @api.multi
    def check_backdate(self):
        self.ensure_one()
        if not self.backdate_start or not self.backdate_finished:
            raise UserError(_("Harap Isi Tanggal Mulai Dan Selesai Process %s") % self.name)

    @api.multi
    def button_receive_good(self):
        self.check_backdate()
        for order in self:
            picking_dict = dict()
            if not order.location_reject_id:
                order.set_location_reject_id()
            move_ids = self.env['stock.move']
            qc_finished_moves = order.qc_ids.mapped('qc_finished_ids').filtered(lambda x: not x.stock_move_created)
            consume_move_lines = order.production_id.move_raw_ids.filtered(
                lambda x: x.state == 'done' and not x.returned_picking).mapped('active_move_line_ids')
            if qc_finished_moves:
                moves = order.create_finished_moves(qc_finished_moves)

                for qc_finished in qc_finished_moves:
                    for move in moves.filtered(lambda x: x.product_id.id == qc_finished.product_id.id):
                        qc_finished.write({'stock_move_created': True,
                                           'move_id': move.id})
                        move.write({'consume_line_ids': [(6, 0, [x for x in consume_move_lines.ids])]})

                move_ids |= moves

            if move_ids:
                picking_finished_id = order.create_finished_picking(goods=True, rejects=False)
                move_ids.write({'picking_id': picking_finished_id.id})
                for picking_finished in picking_finished_id.move_lines:
                    for receive_line in self.env['mrp_workorder.qc_finished_move'].search(
                            [('move_id', 'in', move_ids.ids)]).filtered(
                        lambda x: not x.picking_id
                                  and x.stock_move_created
                                  and x.product_id.id == picking_finished.product_id.id):
                        receive_line.write({'name': picking_finished_id.name,
                                            'picking_id': picking_finished_id.id})

                picking_dict['picking_finished_id'] = picking_finished_id.id
                picking_finished_id.action_assign()

            move_reject_ids = self.env['stock.move']

            qc_reject_moves = order.qc_ids.mapped('qc_reject_ids').filtered(lambda x: not x.stock_move_created)
            # Jika Input Quantity Good Bersaman Quantity Reject Baru Bikin Picking
            if qc_finished_moves and qc_reject_moves:
                moves_reject = order.create_finished_moves(qc_reject_moves)
                for qc_reject in qc_reject_moves:
                    for move_reject in moves_reject.filtered(lambda x: x.product_id.id == qc_reject.product_id.id):
                        qc_reject.write({'stock_move_created': True,
                                         'move_id': move_reject.id})
                        move_reject.write({'consume_line_ids': [(6, 0, [x for x in consume_move_lines.ids])]})
                move_reject_ids |= moves_reject
            if move_reject_ids:
                picking_reject_id = order.create_finished_picking(goods=False, rejects=True)
                picking_dict['picking_reject_id'] = picking_reject_id.id
                move_reject_ids.write({'picking_id': picking_reject_id.id})
                for picking in picking_reject_id.move_lines:
                    for reject_line in self.env['mrp_workorder.qc_reject_move'].search(
                            [('move_id', 'in', move_reject_ids.ids),
                             ]).filtered(lambda x: not x.picking_id and x.product_id.id == picking.product_id.id):
                        reject_line.write({'name': picking_reject_id.name,
                                           'picking_id': picking_reject_id.id})
                if picking_dict.get('picking_finished_id', False):
                    picking_reject_id.write({'backorder_id': picking_dict['picking_finished_id']})
                picking_reject_id.write({'is_rejected': True})
                picking_reject_id.action_assign()

            # Jika Input Quantity Good Tidak Bersamaan Dengan Quantity Reject Baru Bikin Picking
            finished_move_exist = order.qc_ids.mapped('qc_finished_ids').filtered(lambda x: x.picking_id and x.stock_move_created)
            if (finished_move_exist and qc_reject_moves) or (not finished_move_exist and qc_reject_moves):
                moves_reject = order.create_finished_moves(qc_reject_moves)
                for qc_reject in qc_reject_moves:
                    for move_reject in moves_reject.filtered(lambda x: x.product_id.id == qc_reject.product_id.id):
                        qc_reject.write({'stock_move_created': True,
                                         'move_id': move_reject.id})
                        move_reject.write({'consume_line_ids': [(6, 0, [x for x in consume_move_lines.ids])]})
                move_reject_ids |= moves_reject
            if move_reject_ids:
                picking_reject_id = order.create_finished_picking(goods=False, rejects=True)
                picking_dict['picking_reject_id'] = picking_reject_id.id
                move_reject_ids.write({'picking_id': picking_reject_id.id})
                for picking in picking_reject_id.move_lines:
                    for reject_line in self.env['mrp_workorder.qc_reject_move'].search(
                            [('move_id', 'in', move_reject_ids.ids),
                             ]).filtered(lambda x: not x.picking_id and x.product_id.id == picking.product_id.id):
                        reject_line.write({'name': picking_reject_id.name,
                                           'picking_id': picking_reject_id.id})
                if len(finished_move_exist.mapped('picking_id')) == 1:
                    picking_reject_id.write({'backorder_id': finished_move_exist.mapped('picking_id').id})
                    picking_reject_id.write({'is_rejected': True})
                    picking_reject_id.action_assign()
                else:
                    picking_reject_id.write({'is_rejected': True})
                    picking_reject_id.action_assign()

        return True

    @api.multi
    def create_finished_moves(self, values):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()

        for vals in values:
            for line in vals.prepare_finished_moves():
                done += moves.create(line)
        return done

    @api.multi
    def create_finished_picking(self, goods=False, rejects=False):
        # picking_obj = self.env['stock.picking']
        # picking = self.env['stock.picking'].browse()
        for order in self:
            origin_goods = False
            origin_rejects = False
            location_id = False
            location_dest_id = False

            if (not origin_goods and not location_id) and (not location_dest_id and goods):
                location_id = order.production_id.product_template_id.property_stock_production.id
                location_dest_id = order.production_id.location_dest_id.id
                origin_goods = ''.join('%s:%s' % (order.production_id.name, order.production_id.origin))
            elif (not origin_rejects and not location_id) and (not location_dest_id and rejects):
                location_id = order.production_id.product_template_id.property_stock_production.id
                location_dest_id = order.location_reject_id.id
                origin_rejects = ''.join('Reject Of %s:%s' % (order.production_id.name, order.production_id.origin))

            res = {
                'picking_type_id': order.production_id.picking_type_production.id,
                'partner_id': order.partner_id.id or False,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'origin': origin_goods or origin_rejects ,
                'production_id': order.production_id.id,
                'group_id': order.production_id.procurement_group_id.id,
                'company_id': order.production_id.company_id.id,
                'product_select_type': 'goods',
            }
            return self.env['stock.picking'].create(res)


class MrpWorkOrderQcLine(models.Model):
    _name = 'mrp.workorder.qc.line'
    _rec_name = 'product_id'
    _description = 'QC Line'
    _order = 'id'

    @api.one
    @api.depends('qc_good', 'qc_reject', 'qc_sample')
    def _compute_qty_produced(self):
        self.qty_produced = self.qc_good + self.qc_reject + self.qc_sample
        return True

    workorder_id = fields.Many2one(comodel_name="mrp.workorder", string="Order Workorder",
                                   ondelete="cascade", index=True)
    sequence = fields.Integer('Sequence', default=1)

    backdate_start = fields.Datetime(string="Effective Start Date", related="workorder_id.backdate_start")
    backdate_finished = fields.Datetime(string="Effective End Date", related="workorder_id.backdate_finished")

    qc_good = fields.Float(string="QC Good", digits=dp.get_precision('Product Unit of Measure'))
    qc_reject = fields.Float(string="QC Reject", digits=dp.get_precision('Product Unit of Measure'))
    qc_sample = fields.Float(string="QTY Sample", digits=dp.get_precision('Product Unit of Measure'))
    receive_good = fields.Float(string="WH/IN", digits=dp.get_precision('Product Unit of Measure'),
                                compute="compute_receive_good")

    qty_produced = fields.Float(string="Qty Produced", digits=dp.get_precision('Product Unit of Measure'),
                                compute="_compute_qty_produced",
                                help="Jumlah Quantity Yand DiProduksi Dari QC GOOD dan QC REJECT"
                                     "\n Digunakan Untuk Mengecek Sisa Quantity Yang Bisa Diinput")

    state = fields.Selection([
        ('process', 'On Process'),
        ('waiting', 'Waiting Approval'),
        ('reject', 'Reject'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='process', track_visibility='onchange')

    work_order_state = fields.Selection(string="State Work Order", related="workorder_id.state")

    # Tambahan Setelah Presentasi 25 April 2019
    product_id = fields.Many2one(comodel_name="product.product", string="Products")
    product_uom_id = fields.Many2one(
        'product.uom', 'Product Unit of Measure')
    product_qty = fields.Float('Quantity To Produce', default=1.0, digits=dp.get_precision('Product Unit of Measure'))
    ratio = fields.Float('Ratio', digits=dp.get_precision('Product Unit of Measure'))

    # field untuk cek posisi
    next_work_order_id = fields.Many2one(comodel_name="mrp.workorder", related="workorder_id.next_work_order_id",
                                         string="Next Work Order")
    is_cutting = fields.Boolean(string="Is Cutting", related="workorder_id.is_cutting")
    production_id = fields.Many2one(comodel_name="mrp.production", string="Manufacturing Order",
                                    related="workorder_id.production_id")
    is_updated_from_prev_workorder = fields.Boolean(string="Is Updated From Prev Work Order", readonly=True)

    progress_record_ids = fields.One2many(comodel_name="workorder_qc.log.line", inverse_name="qc_id",
                                          string="Progress Record")
    qc_finished_ids = fields.One2many(comodel_name="mrp_workorder.qc_finished_move", inverse_name="qc_id",
                                      string="Product Finished Move")
    qc_reject_ids = fields.One2many(comodel_name="mrp_workorder.qc_reject_move", inverse_name="qc_id",
                                    string="Product Finished Reject Move")

    is_work_order_finishing = fields.Boolean(string="Check Work Order Finishing", compute="_compute_workorder_type")
    is_locked = fields.Boolean('Is Locked', default=True, copy=False)

    picking_count = fields.Integer(string="STBJ Count", compute="_compute_picking_count")

    def _compute_picking_count(self):
        for line in self:
            picking_finished = line.qc_finished_ids.mapped('picking_id')
            picking_reject = line.qc_reject_ids.mapped('picking_id')
            line.picking_count = len(picking_finished) + len(picking_reject)
            # read_group_finished_res = self.env['mrp_workorder.qc_finished_move'].read_group(
            #     [('qc_id', 'in', self.ids), ('picking_id', '!=', False)], ['picking_id', 'qc_id'], ['qc_id'])
            # mapped_data_finished = dict([(data['qc_id'][0], data['qc_id_count']) for data in read_group_finished_res])
            # # read_group(domain, fields, groupby, offset, limit, orderby, lazy)

    @api.depends('next_work_order_id', 'is_cutting')
    def _compute_workorder_type(self):
        for line in self:
            if not line.next_work_order_id and not line.is_cutting:
                line.is_work_order_finishing = True
            else:
                line.is_work_order_finishing = False

    @api.multi
    @api.depends('production_id.move_finished_ids',
                 'production_id.move_finished_ids.quantity_done')
    def compute_receive_good(self):
        for line in self:
            quantity_done = []
            for move in line.production_id.move_finished_ids.filtered(
                    lambda x:x.product_id.id == line.product_id.id and x.state == 'done'):
                quantity_done.append(move.quantity_done)
            if quantity_done:
                line.receive_good = sum(quantity_done)

    # def prepare_finished_moves(self):
    #     self.ensure_one()
    #     res = []
    #     if self.product_id.type not in ['product', 'consu']:
    #         return res
    #     result_plan = self._compute_price_unit()
    #     total_unit_cost = []
    #     if self.product_id:
    #         for line in result_plan['lines']:
    #             if (line.get('attribs') == self.product_id.mapped('attribute_value_ids')[0].name) or (line.get('attribs') == self.product_id.mapped('attribute_value_ids')[1].name):
    #                 total_unit_cost.append(line['unit_cost'])
    #
    #     location_id = self.production_id.product_template_id.property_stock_production.id
    #     location_dest_id = self.production_id.location_dest_id.id
    #     template = {
    #         'picking_type_id': self.production_id.picking_type_production.id,
    #         'partner_id': self.workorder_id.partner_id.id,
    #         'name': ''.join('%s:%s' % (self.production_id.name, self.product_id.display_name)),
    #         'date': self.production_id.date_planned_start,
    #         'date_expected': self.production_id.date_planned_start,
    #         'product_id': self.product_id.id,
    #         'price_unit': sum(total_unit_cost),
    #         'product_uom': self.product_uom_id.id,
    #         'product_uom_qty': self.qc_good + self.qc_sample,
    #         'location_id': location_id,
    #         'location_dest_id': location_dest_id,
    #         'company_id': self.production_id.company_id.id,
    #         'production_id': self.production_id.id,
    #         'origin': self.production_id.name,
    #         'group_id': self.production_id.procurement_group_id.id,
    #         'propagate': self.production_id.propagate,
    #         'move_dest_ids': [(4, x.id) for x in self.production_id.move_dest_ids],
    #         'state': 'draft',
    #     }
    #     res.append(template)
    #     return res

    @api.multi
    def button_done(self):
        if self.work_order_state != 'progress':
            raise UserError(_("Anda Belum Memulai Pekerjaan"
                              "\n Klik Tombol Start Working Untuk Memproses Inputan"))
        if not self.qc_good:
            raise UserError(_("Anda Harus Input Quantity Good Terlebih Dahulu"))
        # self.check_qty_produced()
        if self.qty_produced > self.product_qty:
            self.write({'state': 'waiting'})

        elif self.qty_produced < self.product_qty:
            self.write({'state': 'waiting'})

        elif self.qty_produced == self.product_qty:
            self.update_current_qty()
            self.check_next_workorder()

            self.write({'state': 'done'})



        # if self.is_work_order_finishing:
        #     self.update_current_qty()
        #     self.write({'state': 'done'})
        return True

    @api.multi
    def update_current_qty(self):
        if self.next_work_order_id and self.is_cutting:
            self.workorder_id.qc_done += self.qc_good

        if self.next_work_order_id and not self.is_cutting:
            self.workorder_id.qc_done += self.qc_good
            self.next_work_order_id.write({'qty_producing': self.qc_good})
            self.update_next_qty_variant()

        if not self.next_work_order_id and not self.is_cutting:
            self.workorder_id.qc_done += self.qc_good
            self.workorder_id.qc_done += self.qc_sample
            # self.update_move_finished_uom_qty()

        return True

    @api.multi
    def check_next_workorder(self):
        for order in self:
            next_workorder = order.workorder_id.next_work_order_id
            is_cutting = order.workorder_id.is_cutting

            if next_workorder and not is_cutting:
                check_current_qty = next_workorder.qty_producing
                if check_current_qty != order.workorder_id.qc_done:
                    next_workorder.write({'qty_producing': order.workorder_id.qc_done})
        return True

    @api.multi
    def update_next_qty_variant(self):
        products = self.next_work_order_id.qc_ids.filtered(
            lambda x: (x.product_id.id == self.product_id.id) and (x.state != 'done'))
        if products:
            products.write({'product_qty': self.qc_good,
                            'is_updated_from_prev_workorder': True})

        return True

    @api.multi
    def button_approve(self):
        self.update_current_qty()
        self.check_next_workorder()
        self.write({'state': 'done'})
        return True

    @api.multi
    def button_reject(self):
        # self.workorder_id.qc_done -= self.qc_good
        self.update({'qc_good': 0.0,
                     'qc_reject': 0.0,
                     'qc_sample': 0.0})
        self.write({'state': 'reject'})

        return True

    @api.multi
    def check_update_next_qty_variant(self):
        products = self.next_work_order_id.qc_ids.filtered(
            lambda x: (x.product_id.id == self.product_id.id) and (x.state == 'done'))
        if products:
            raise UserError(_("Tidak Bisa Direset Karena Workorder %s"
                              "\n Inputannya Sedang Dalam Proses") % self.next_work_order_id.name)


class QcLogLine(models.Model):
    _name = 'workorder_qc.log.line'
    _rec_name = 'product_id'
    _description = 'Log Input Quantity Good Dan Quantity Reject'

    qc_id = fields.Many2one(comodel_name="mrp.workorder.qc.line", string="Order Qc", ondelete="cascade", index=True)
    product_id = fields.Many2one(comodel_name="product.product", string="Products")
    date_start = fields.Datetime('Date', copy=False, index=True, readonly=True)
    quantity_good = fields.Float(string="Quantity Good", digits=dp.get_precision('Product Unit of Measure'))
    quantity_reject = fields.Float(string="Quantity Reject", digits=dp.get_precision('Product Unit of Measure'))
    quantity_sample = fields.Float(string="Quantity Sample", digits=dp.get_precision('Product Unit of Measure'))

    user_id = fields.Many2one('res.users', 'Responsible')

    state_log_line = fields.Selection(string="Status Input",
                                      selection=[('added', 'Added'),
                                                 ('adjustment', 'Adjustment'), ],
                                      readonly=True, index=True, copy=False, track_visibility='onchange')

    # @api.depends('qc_id', 'qc_id.next_work_order_id', 'qc_id.is_cutting')
    # def _compute_picking_reference(self):
    #     for line in self:
    #         next_work_order_id, is_cutting = line.qc_id.next_work_order_id, line.qc_id.is_cutting
    #         production_id = line.qc_id.production_id
    #         if not next_work_order_id and not is_cutting:
    #             line.name = line.get_picking_reference(production_id, line.product_id)
    #     return True
    #
    # @api.multi
    # def get_picking_reference(self, production_id, product_id):
    #     move_object = self.env['stock.move']
    #     picking_reference = False
    #     if not picking_reference:
    #         picking_reference = move_object.search(
    #             [('production_id', '=', production_id.id),
    #              ('product_id', '=', product_id.id)], limit=1)
    #     return picking_reference.picking_id.name or False


class MrpQcReject(models.Model):
    _name = 'mrp_workorder.qc_reject_move'
    _rec_name = 'name'
    _description = 'Product Finished Reject Move'

    name = fields.Char(string="Reference Number")
    picking_id = fields.Many2one(comodel_name="stock.picking", string="Picking Reference")
    move_id = fields.Many2one(comodel_name="stock.move", string="Move Reference")
    qc_log_id = fields.Many2one(comodel_name="workorder_qc.log.line", string="QC Log Reference")
    qc_id = fields.Many2one(comodel_name="mrp.workorder.qc.line", string="QC Reference")

    product_id = fields.Many2one(comodel_name="product.product", string="Products")
    product_qty = fields.Float(string="Quantity", digits=dp.get_precision('Product Unit of Measure'))
    product_uom_id = fields.Many2one(
        'product.uom', 'Product Unit of Measure')

    backdate_start = fields.Datetime(string="Effective Start Date", related="qc_id.backdate_start")
    backdate_finished = fields.Datetime(string="Effective End Date", related="qc_id.backdate_finished")

    stock_move_created = fields.Boolean(string="Product Moves Created")
    move_state = fields.Selection(string="State", related="picking_id.state")

    def _compute_price_unit(self):
        for order in self:
            plan_id = order.qc_id.production_id.mapped('assembly_plan_id')
            values = self.env['report.textile_assembly.assembly_plan_cost_report'].get_lines(plan_id)

            result = {'lines': values}
            return result

    def prepare_finished_moves(self):
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        result_plan = self._compute_price_unit()
        total_unit_cost = []
        if self.product_id:
            for line in result_plan['lines']:
                if (line.get('attribs') == self.product_id.mapped('attribute_value_ids')[0].name) or (
                        line.get('attribs') == self.product_id.mapped('attribute_value_ids')[1].name):
                    total_unit_cost.append(line['unit_cost'])

        location_id = self.product_id.property_stock_production.id
        location_dest_id = self.qc_id.workorder_id.location_reject_id.id

        # location_id = self.production_id.product_template_id.property_stock_production.id
        # location_dest_id = self.production_id.location_dest_id.id
        template = {
            'picking_type_id': self.qc_id.production_id.picking_type_production.id,
            'partner_id': self.qc_id.workorder_id.partner_id.id,
            'name': ''.join('%s:%s' % (self.qc_id.production_id.name, self.product_id.display_name)),
            'date': self.backdate_start,
            'date_expected': self.backdate_finished,
            'product_id': self.product_id.id,
            'price_unit': sum(total_unit_cost),
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': self.product_qty,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'company_id': self.qc_id.production_id.company_id.id,
            'production_id': self.qc_id.production_id.id,
            'origin': ''.join('%s:%s' % (self.qc_id.production_id.name, self.qc_id.production_id.origin)),
            'group_id': self.qc_id.production_id.procurement_group_id.id,
            'propagate': self.qc_id.production_id.propagate,
            'move_dest_ids': [(4, x.id) for x in self.qc_id.production_id.move_dest_ids],
            'state': 'draft',
        }
        res.append(template)
        return res


class MrpQcFinished(models.Model):
    _name = 'mrp_workorder.qc_finished_move'
    _rec_name = 'name'
    _description = 'Products Finished Move'

    name = fields.Char(string="Reference Number")
    picking_id = fields.Many2one(comodel_name="stock.picking", string="Picking Reference")
    move_id = fields.Many2one(comodel_name="stock.move", string="Move Reference")
    qc_log_id = fields.Many2one(comodel_name="workorder_qc.log.line", string="QC Log Reference")
    qc_id = fields.Many2one(comodel_name="mrp.workorder.qc.line", string="QC Reference")

    product_id = fields.Many2one(comodel_name="product.product", string="Products")
    product_qty = fields.Float(string="Quantity", digits=dp.get_precision('Product Unit of Measure'))
    product_uom_id = fields.Many2one(
        'product.uom', 'Product Unit of Measure')

    backdate_start = fields.Datetime( string="Effective Start Date", related="qc_id.backdate_start")
    backdate_finished = fields.Datetime(string="Effective End Date", related="qc_id.backdate_finished")

    stock_move_created = fields.Boolean(string="Product Moves Created")
    move_state = fields.Selection(string="State", related="picking_id.state")

    def _compute_price_unit(self):
        for order in self:
            plan_id = order.qc_id.production_id.mapped('assembly_plan_id')
            values = self.env['report.textile_assembly.assembly_plan_cost_report'].get_lines(plan_id)

            result = {'lines': values}
            return result

    def prepare_finished_moves(self):
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        result_plan = self._compute_price_unit()
        total_unit_cost = []
        if self.product_id:
            for line in result_plan['lines']:
                if (line.get('attribs') == self.product_id.mapped('attribute_value_ids')[0].name) or (line.get('attribs') == self.product_id.mapped('attribute_value_ids')[1].name):
                    total_unit_cost.append(line['unit_cost'])

        location_id = self.product_id.property_stock_production.id
        location_dest_id = self.qc_id.production_id.location_dest_id.id

        # location_id = self.production_id.product_template_id.property_stock_production.id
        # location_dest_id = self.production_id.location_dest_id.id
        template = {
            'picking_type_id': self.qc_id.production_id.picking_type_production.id,
            'partner_id': self.qc_id.workorder_id.partner_id.id,
            'name': ''.join('%s:%s' % (self.qc_id.production_id.name, self.product_id.display_name)),
            'date': self.backdate_start,
            'date_expected': self.backdate_finished,
            'product_id': self.product_id.id,
            'price_unit': sum(total_unit_cost),
            'product_uom': self.product_uom_id.id,
            'product_uom_qty': self.product_qty,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'company_id': self.qc_id.production_id.company_id.id,
            'production_id': self.qc_id.production_id.id,
            'origin': ''.join('%s:%s' % (self.qc_id.production_id.name, self.qc_id.production_id.origin)),
            'group_id': self.qc_id.production_id.procurement_group_id.id,
            'propagate': self.qc_id.production_id.propagate,
            'move_dest_ids': [(4, x.id) for x in self.qc_id.production_id.move_dest_ids],
            'state': 'draft',
        }
        res.append(template)
        return res


class MrpWorkorderServiceLine(models.Model):
    _name = 'mrp.workorder.service.line'
    _rec_name = 'product_id'
    _description = 'List Product Service'

    work_order_id = fields.Many2one(comodel_name="mrp.workorder", string="Order WorkOrder",
                                    ondelete="cascade", index=True)
    production_id = fields.Many2one(comodel_name='mrp.production', string='Production_id', related="work_order_id.production_id")
    product_id = fields.Many2one(comodel_name="product.product", string="Products",
                                 track_visibility='onchange', domain=[('type', '=', 'service')])
    product_qty = fields.Float(string="Quantity Per Pcs", digits=dp.get_precision('Product Unit of Measure'))
    product_uom_id = fields.Many2one(comodel_name="product.uom", string="UoM",
                                     related="product_id.uom_id")
    price_unit = fields.Float(string="Unit Price", digits=dp.get_precision('Product Price'))
    has_po = fields.Boolean(string='Has_po', compute="_has_po")

    @api.depends('production_id')
    def _has_po(self):
        for service in self:
            workorder_ids = service.production_id.mapped('workorder_ids')
            product_ids = service._get_product_inpurchase(workorder_ids)
            if product_ids:
                service.has_po = service.product_id in product_ids

    def _get_product_inpurchase(self, work_order_ids):
        purchase_ids = self.env['purchase.order'].search([('work_order_id', 'in', work_order_ids.ids)])
        product_ids = []
        if purchase_ids:
            for purchase_id in purchase_ids:
                for line in self.env['purchase.order.line'].browse(purchase_id.id):
                    product_ids.append(line.product_id)
        return product_ids






