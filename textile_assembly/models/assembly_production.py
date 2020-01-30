from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import html2plaintext


class AssemblyProd(models.Model):
    _name = 'assembly.production'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _date_name = 'date_planned_start'
    _description = 'Assembly Production'
    _order = 'date_planned_start asc,id'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('product_tmpl_id.name', operator, name)]
        pos = self.search(domain + args, limit=limit)
        return pos.name_get()

    state = fields.Selection([
        ('draft', 'Draft'),
        ('process', 'On Process'),
        ('waiting', 'Waiting On Approval'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')

    name = fields.Char('Assembly Reference', copy=False, readonly=True, default=lambda x: _('New'),
                       track_visibility='onchange')

    date_planned_start = fields.Datetime(
        'Scheduled Date Start', copy=False,
        states={'approve': [('readonly', True)], 'cancel': [('readonly', True)]})
    date_planned_finished = fields.Datetime(
        'Scheduled Date Finished', copy=False,
        states={'approve': [('readonly', True)], 'cancel': [('readonly', True)]})

    product_tmpl_id = fields.Many2one(comodel_name="product.template", string="Product To Produce",
                                      index=True, track_visibility='onchange', ondelete='cascade',
                                      help="Acuan Produk Yang Akan Diproduksi")
    product_categ_id = fields.Many2one(comodel_name="product.category",
                                       related="product_tmpl_id.categ_id", string="Category Product",
                                       index=True, readonly=True)
    partner_id = fields.Many2one(comodel_name="res.partner", string="CMT Vendor", required=True,
                                 track_visibility='onchange', states={'approve': [('readonly', True)],
                                                                      'cancel': [('readonly', True)]})
    pattern_code = fields.Char(string="Code Pola", related="product_tmpl_id.pattern_code")
    user_id = fields.Many2one('res.users', string='Responsible', index=True, track_visibility='onchange',
                              default=lambda self: self.env.user, copy=False)
    version = fields.Integer(string="Ver", default=1, index=True)
    active = fields.Boolean('Active Assembly', default=True, index=True,
                            help="Jika Tidak Dicentang Document Assembly Tidak Tampil Di View")

    variant_line_ids = fields.One2many(comodel_name="assembly.prod.variant.line", inverse_name="assembly_id",
                                       string="Component Product", help="Standard Produksi Untuk Membuat Produk Jadi",
                                       copy=True)
    raw_material_line_ids = fields.One2many(comodel_name="assembly.raw.material.line", inverse_name="assembly_id",
                                            string="Raw Materials", help="Kebutuhan Bahan Baku Pada Produksi",
                                            copy=True)
    cmt_material_line_ids = fields.One2many(comodel_name="assembly.cmt.material.line", inverse_name="assembly_id",
                                            string="Aksesoris", help="Kebutuhan Bahan Pembantu Pada Produksi",
                                            copy=False)
    cmt_template_ids = fields.One2many(comodel_name="assembly.cmt.product.template", inverse_name="assembly_id",
                                       string="CMT Aksesoris", help="Record Produk Variant Untuk Bahan Pembantu",
                                       copy=True)
    cmt_service_ids = fields.One2many(comodel_name="assembly.cmt.product.service", inverse_name="assembly_id",
                                      string="Biaya Jasa Produksi",
                                      help="Biaya Biaya Produksi Yang Perlu Dibayar Untuk Memproduksi",
                                      copy=True)

    amount_total_text = fields.Text(string="Grand Total", compute="_compute_amount_total_text",
                                    help="Total Biaya Keseluruhan Pada Tiap Produk Variant")
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  states={'cancel': [('readonly', True)], 'approve': [('readonly', True)]},
                                  default=lambda self: self.env.user.company_id.currency_id.id)

    product_image = fields.Binary('photo', attachment=True)
    product_uom_id = fields.Many2one(
        'product.uom', 'Product Unit of Measure', related="product_tmpl_id.uom_id")
    routing_id = fields.Many2one(comodel_name="mrp.routing", string="Routing", track_visibility='onchange')
    assembly_plan_ids = fields.One2many(comodel_name="assembly.plan", inverse_name="assembly_id", string="#Plans")
    plan_count = fields.Integer(string="# Plans", compute="_compute_plan_count")
    bom_ids = fields.One2many(comodel_name="mrp.bom", inverse_name="assembly_prod_id", string="BOMs")
    bom_count = fields.Integer(string="# BOMs", compute="_compute_bom_count")
    mo_done = fields.Boolean(string="MO Done", compute="_compute_mo_done")

    @api.multi
    @api.depends('assembly_plan_ids')
    def _compute_mo_done(self):
        for assembly in self:
            mo_done = assembly.assembly_plan_ids.mapped('mo_ids')
            assembly.mo_done = all(mo.state == 'done' for mo in mo_done) if mo_done else False

    @api.multi
    @api.depends('name', 'product_tmpl_id.name')
    def name_get(self):
        result = []
        for assembly in self:
            name = assembly.name
            if assembly.product_tmpl_id:
                name += ' (' + assembly.product_tmpl_id.name + ')'
            result.append((assembly.id, name))
        return result

    @api.multi
    def _compute_amount_total_text(self):
        """ Menghitung Total Keseluruhan Biaya Pada Tiap Variant
         :return total_amount_text """
        # assemblies = self
        # report_model = self.env['report.textile_assembly.assembly_production_cost_report']
        # # Panggil Fungsi Report Untuk Mengenerate Total Variant
        # value_ids = report_model.get_lines(assemblies)
        # result = {'lines': value_ids}
        # amount_total_text = ''.join('%s:' % (line['attributes']) + '{:,.2f}\n' .format(line['total'])
        #                             for line in result['lines'])

        for assembly in self:
            report_model = self.env['report.textile_assembly.assembly_production_cost_report']
            value_ids = report_model.get_lines(assembly)
            if value_ids:
                result = {'lines': value_ids}
                amount_total_text = ''.join('%s:' % (line['attributes']) + '{:,.2f}\n'.format(line['total'])
                                            for line in result['lines'])
                assembly.amount_total_text = html2plaintext(amount_total_text)
            else:
                return None

    @api.multi
    def _compute_plan_count(self):
        # Kelompokan ID assembly pada model assembly plan Dalam Format Dictionary
        read_group_res = self.env['assembly.plan'].read_group([('assembly_id', 'in', self.ids)], ['assembly_id'],
                                                              ['assembly_id'])
        mapped_data = dict([(data['assembly_id'][0], data['assembly_id_count']) for data in read_group_res])
        for assembly in self:
            assembly.plan_count = mapped_data.get(assembly.id, 0)

    @api.multi
    def _compute_bom_count(self):
        # Kelompokan Id Assembly pada model mrp bom Dalam Format Dictionary
        read_group_res = self.env['mrp.bom'].read_group([('assembly_prod_id', 'in', self.ids)], ['assembly_prod_id'],
                                                        ['assembly_prod_id'])
        mapped_data = dict([(data['assembly_prod_id'][0], data['assembly_prod_id_count']) for data in read_group_res])
        for bom in self:
            bom.bom_count = mapped_data.get(bom.id, 0)

    @api.multi
    def check_selected_routing_id(self):
        """Cek Apakah Terdapat Work Center Cutting Pada Routing Yang Dipilih"""
        for assembly in self:
            workcenter_ids = assembly.routing_id.operation_ids.mapped('workcenter_id')
            if not any(workcenter.is_cutting for workcenter in workcenter_ids):
                raise UserError(_("Tidak Ditemukan Work Center Yang Bertipe Cutting Pada Routing %s\n"
                                  "Anda Harus Mencentang Cutting Pada Salah Satu Workcenter Pada Routing ini")
                                % assembly.routing_id.name)

        return True

    @api.onchange('routing_id')
    def _onchange_routing_id(self):
        routing_ids = self.compute_routing_cutting()
        domain = {'routing_id': [('id', 'in', routing_ids.ids)]}
        result = {'domain': domain}
        return result

    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        product_ids = self._get_product_finish_goods()
        domain = {'product_tmpl_id': [('id', 'in', product_ids)]}
        result = {'domain': domain}
        return result

    @api.multi
    def _get_product_finish_goods(self):
        product_object = self.env['product.template']
        product_ids = []
        for product in product_object.search(
                [('template_code', '!=', False),
                 ('pattern_code', '!=', False),
                 ('sale_ok', '=', True),
                 ('purchase_ok', '=', False)]):
            product_ids.append(product.id)
        return product_ids

    @api.multi
    def compute_routing_cutting(self):
        operation_ids = self.env['mrp.routing'].search([]).mapped('operation_ids')
        routing_ids = operation_ids.filtered(lambda x: x.workcenter_id.is_cutting).mapped('routing_id')
        return routing_ids

    @api.multi
    def action_assembly_plan_create(self):
        assembly_plan_model = self.env['assembly.plan']
        for order in self:
            plan_domain = assembly_plan_model.search([('assembly_id', '=', order.id)])
            if not plan_domain:
                res = {
                    'assembly_id': order.id,
                    'product_uom_id': order.product_uom_id.id,
                    'origin': order.name,
                    'product_template_id': order.product_tmpl_id.id,
                    'partner_id': order.partner_id.id,
                    'date_planned_start': order.date_planned_start,
                    'date_planned_finished': order.date_planned_finished,
                }
                plan_id = assembly_plan_model.create(res)
            else:
                # Jika Ada Select Dokumen Yang Sudah Ada
                plan_id = plan_domain[0]
            # Siapkan Data Lainya
            order.variant_line_ids.generate_assembly_plan_line(plan_id)
            order.raw_material_line_ids.generate_assembly_plan_raw_material(plan_id)
            order.cmt_material_line_ids.generate_assembly_plan_cmt_material(plan_id)
            order.cmt_service_ids.generate_assembly_plan_services(plan_id)
            order.action_create_assembly_plan_produce(plan_id)

        return True

    @api.multi
    def action_create_assembly_plan_produce(self, plan_id):
        attribute_ids = self.raw_material_line_ids.mapped('attribute_id')
        plan_produces = self.env['assembly.plan.produce']
        for line in attribute_ids:
            plan_produces |= self.env['assembly.plan.produce'].create({'attribute_id': line.id,
                                                                       'plan_id': plan_id.id})
        return plan_produces

    @api.multi
    def action_generate_assembly_bom(self):
        for assembly in self:
            assembly.act_bom_create()

            bom_id = assembly.bom_ids.filtered(lambda x: x.assembly_prod_id)
            if bom_id:
                assembly.cmt_service_ids.write({'bom_id': bom_id[0].id})

        return True

    @api.multi
    def act_bom_create(self):
        result = {}
        bom_model = self.env['mrp.bom']
        for assembly in self:
            bom_ids = self.env['mrp.bom']
            quantity_bom = [variant.ratio for variant in assembly.variant_line_ids]
            bom_id = bom_model.create({
                'product_tmpl_id': assembly.product_tmpl_id.id,
                'product_qty': sum(quantity_bom),
                'product_uom_id': assembly.product_uom_id.id,
                'code': assembly.name,
                'routing_id': assembly.routing_id.id,
                'assembly_prod_id': assembly.id
            })
            bom_ids |= bom_id
            for raw_material in assembly.raw_material_line_ids:
                bom_ids.update({
                    'bom_line_ids': [(0, 0, {
                        'product_id': raw_material.product_id.id,
                        'product_qty': raw_material.product_qty,
                        'product_uom_id': raw_material.product_uom_id.id
                    })]
                })
            for cmt_material in assembly.cmt_material_line_ids:
                bom_ids.update({
                    'bom_line_ids': [(0, 0, {
                        'product_id': cmt_material.product_id.id,
                        'product_qty': cmt_material.product_qty,
                        'product_uom_id': cmt_material.product_uom_id.id
                    })]
                })
            assert len(bom_ids) == 1
            result[assembly.id] = bom_ids.id

        return result

    @api.multi
    def _set_product_variant_line(self):
        """
        Ketika User Memencet Tombol Confirm Saat Status Draft.
        Tabel Product Component Terisi Sesuai Variant Product Tsb
        """
        variant_model = self.env['assembly.prod.variant.line']
        for assembly in self:
            product_variant_ids = assembly.product_tmpl_id.product_variant_ids

            for product_variant in product_variant_ids:
                product_values = {
                    'product_id': product_variant.id,
                    # 'attribute_value_ids': [(6, 0, product_variant.attribute_value_ids.ids)],
                    'assembly_id': assembly.id,
                }
                variant_model |= self.env['assembly.prod.variant.line'].create(product_values)

        return variant_model

    @api.multi
    def _unset_product_variant_line(self):
        for assembly in self:
            if assembly.variant_line_ids:
                product_id = assembly.variant_line_ids.mapped('product_id').mapped('product_tmpl_id')
                if product_id.id != assembly.product_tmpl_id.id:
                    assembly.variant_line_ids.unlink()
                    assembly._set_product_variant_line()
                else:
                    return False
        return True

    @api.multi
    def _action_create_cmt_line(self):
        self.ensure_one()
        product_non_attributes, product_attributes = self.compute_product_variant_attributes()

        self.action_create_cmt_lines(product_non_attributes, product_attributes)

    @api.multi
    def action_create_cmt_lines(self, product_non_attributes, product_attributes):
        cmt_line_model = self.env['assembly.cmt.material.line']
        for attrib in product_attributes:
            if attrib.product_id:
                product_variant_ids = attrib.product_id.mapped('product_variant_ids')
                product_list_select = self.get_product_list_select(product_variant_ids)
                for line in product_list_select:
                    cmt_line_model.create({
                        'assembly_id': attrib.assembly_id.id,
                        'product_id': line.id,
                        'product_qty': attrib.product_qty,
                        'product_uom_id': attrib.product_uom_id.id,
                        'price_unit': attrib.price_unit,
                        'sequence': attrib.sequence
                    })

        for non_attrib in product_non_attributes:
            if non_attrib.product_id:
                product_non_variants = non_attrib.product_id.mapped('product_variant_ids')
                for product_non_variant in product_non_variants:
                    cmt_line_model.create({
                        'assembly_id': non_attrib.assembly_id.id,
                        'product_id': product_non_variant.id,
                        'product_qty': non_attrib.product_qty,
                        'product_uom_id': non_attrib.product_uom_id.id,
                        'price_unit': non_attrib.price_unit,
                        'sequence': non_attrib.sequence
                    })

    @api.multi
    def compute_product_variant_attributes(self):
        """
        Filter Product Yang Berattribute Dan Non pada model assembly.cmt.template
        :return: list product yang berattribut dan non attribute
        """
        for assembly in self:
            product_non_attributes = assembly.cmt_template_ids.filtered(lambda x: not x.product_id.attribute_line_ids)
            product_attributes = assembly.cmt_template_ids.filtered(lambda x: x.product_id.attribute_line_ids)
            return product_non_attributes, product_attributes

    @api.multi
    def get_product_list_select(self, product_variant_ids):
        """
        Filter Product Sesuai Attribute Pada Model assembly.prod.variant.line
        :param product_variant_ids:
        :return: list product yang telah difilter
        """
        for assembly in self:
            set_attributes = assembly.variant_line_ids.mapped('attribute_value_ids')
            if set_attributes:
                return [variant for variant in product_variant_ids.filtered(
                    lambda x: x.attribute_value_ids in set_attributes)]

    @api.multi
    def update_cmt_ratio(self):
        """
        Hitung Total Ratio Pada Product Berattribute Maupun Non Attribute
        Reference Model assembly.prod.variant.line
        :return: dict
        """
        self.ensure_one()
        # Update Ratio Pada model assembly.cmt.material.line
        product_attributes = self.cmt_material_line_ids.filtered(
            lambda x: x.product_id and x.product_id.attribute_value_ids)

        if product_attributes:
            for cmt_line in product_attributes:
                if cmt_line.product_id:
                    set_attributes = cmt_line.product_id.mapped('attribute_value_ids')
                    total_ratio_list = [variant.ratio for variant in self.variant_line_ids.filtered(
                        lambda x: (x.attribute_value_ids[0] in set_attributes)
                                  or (x.attribute_value_ids[1] in set_attributes))]
                    cmt_line.update({'ratio': sum(total_ratio_list)})

        product_non_attributes = self.cmt_material_line_ids.filtered(
            lambda x: x.product_id and not x.product_id.attribute_value_ids)
        if product_non_attributes:
            for cmt_line in product_non_attributes:
                if cmt_line.product_id:
                    total_ratio_list = [variant.ratio for variant in self.variant_line_ids]
                    cmt_line.update({'ratio': sum(total_ratio_list)})

        return True

    @api.multi
    def compare_ratio(self):
        """
        Hitung Total Ratio Untuk Product Berattribute Pada Model assembly.raw.material.line
        :return: sum(list)
        """
        for assembly in self:
            for raw in assembly.raw_material_line_ids:
                if raw.product_id and raw.attribute_id:
                    total_ratio = [variant.ratio for variant in assembly.variant_line_ids.filtered(
                        lambda x: (x.attribute_value_ids[0] in raw.attribute_id)
                                  or (x.attribute_value_ids[1] in raw.attribute_id))]
                    raw.update({'ratio': sum(total_ratio)})

    @api.multi
    def compute_count_product_tmpl_id(self):
        """
        Hitung Total Record Yang Terbentuk Dengan Product Identical
        :return: int
        """
        assembly_object = self.env['assembly.production']
        counter = 1
        for assembly in self:
            counters = assembly_object.search_read([('product_tmpl_id', '=', assembly.product_tmpl_id.id),
                                                    ('id', 'not in', assembly.ids)], order='id')

            if not counters:
                return counter
            elif counters:
                count_version = counters[-1]['version']
                return count_version + 1

    @api.multi
    def action_create_name_reference(self, count_number=None):
        """
        Format Nama Assembly Reference
        :param count_number:
        :return: str
        """
        for assembly in self:
            name, version, product_code = assembly.product_tmpl_id.name, count_number, assembly.product_tmpl_id.template_code
            return ''.join('%s %s V%s' % (name, product_code, str(version)))

    @api.multi
    def do_print_picking(self):
        return self.env.ref('textile_assembly.action_report_assembly_price').report_action(self)

    # Button
    @api.multi
    def button_process(self):
        self.ensure_one()
        self.check_selected_routing_id()

        if not self.variant_line_ids:
            self._set_product_variant_line()
        else:
            self._unset_product_variant_line()

        product_code = self.product_tmpl_id.template_code
        if not product_code:
            raise UserError(_("Update Code Produk Terlebih Dahulu"))
        # Count product_tmpl_id yang sama
        count_number = self.compute_count_product_tmpl_id()

        name = self.action_create_name_reference(count_number=count_number)
        values = {'name': name, 'version': count_number, 'state': 'process'}
        return self.write(values)

    @api.multi
    def button_approve(self):
        for assembly in self:
            assembly.write({'state': 'approve'})
            assembly.action_generate_assembly_bom()
            assembly.action_assembly_plan_create()

        return True

    @api.multi
    def button_reject(self):
        for assembly in self:
            assembly.write({'state': 'reject'})
            assembly.cmt_material_line_ids.unlink()

        return True

    @api.multi
    def button_cancel(self):
        for assembly in self:
            plan_process = assembly.assembly_plan_ids.filtered(lambda x: x.assembly_id.id == assembly.id)
            if not plan_process:
                assembly.action_cancel()
            if plan_process:
                if all(plan.state != 'cancel' for plan in plan_process):
                    raise UserError(_('Anda Tidak Dapat Melakukan Cancel Pada Dokumen Ini, '
                                      '\n Karena Dokumen Assembly Plan Yang Terhubung Statusnya On Progress'
                                      '\n Cancel Terlebih Dahulu Dokumen Assembly Plan nya'))
                plan_process.button_cancel()
        return True

    @api.multi
    def check_attribute_material(self):
        raw_material_attributes = self.raw_material_line_ids.mapped('attribute_id')
        variant_attributes = self.variant_line_ids.mapped('attribute_value_ids').filtered(
            lambda attribute_value: attribute_value.attribute_id in raw_material_attributes.mapped('attribute_id')
        )
        unreserve_attribute = []
        for variant in variant_attributes:
            if variant not in raw_material_attributes:
                unreserve_attribute.append(variant)
            # for material in raw_material_attributes:
            #     if variant.id != material.id:
            #         unreserve_attribute.append(variant)
            #     if variant.id == material.id:
            #         continue
        if unreserve_attribute:
            message = ''.join('\t%s\n' % attribute.display_name for attribute in unreserve_attribute)
            raise UserError(_("Beberapa Attribute Belum Diset Pada Raw Material Products\n"
                              "%s") % message)

    @api.multi
    def button_need_approval(self):
        self.check_attribute_material()
        ratio_done = self.variant_line_ids.filtered(lambda x: x.ratio)
        if len(ratio_done) != len(self.variant_line_ids.mapped('ratio')):
            raise UserError(_("Kolum Ratio Perlu Di input Semua"))
        if not self.cmt_template_ids and not self.raw_material_line_ids:
            raise UserError(_("Raw Material Dan CMT Material Harus Diisi Terlebih Dahulu"))
        if not self.cmt_service_ids:
            raise UserError(_("Kolom Biaya Produksi Wajib Diisi"))
        self._action_create_cmt_line()
        self.compare_ratio()
        self.update_cmt_ratio()
        return self.write({'state': 'waiting'})

    @api.multi
    def action_cancel(self):
        for assembly in self:
            assembly.write({'state': 'cancel', 'active': False})

        return True

    @api.multi
    def unlink(self):
        for assembly in self:
            if any(order != 'cancel' for order in assembly.mapped('state')):
                raise UserError(_("Assembly Production Dalam Sedang Proses, Perlu Di Batalkan Lebih Dahulu"))

            plan_process = assembly.assembly_plan_ids.filtered(lambda x: x.assembly_id.id == assembly.id)
            if any(plan.state != 'cancel' for plan in plan_process):
                raise UserError(_('Anda Tidak Dapat Menghapus Assembly Yang Terhubung Dengan Assembly Plan.'
                                  '\nCancel Assembly Plan Telebih Dahulu'))

            if plan_process.mapped('state') == 'cancel':
                plan_process.unlink()

            return super(AssemblyProd, self).unlink()

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {}, active=True)
        return super(AssemblyProd, self).copy(default)























































































