from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class ChangeInputanQty(models.TransientModel):
    _name = 'change.inputan.qty'
    _description = 'Hanya Inputan Quantity Good Dan Quantity Reject'

    name = fields.Char(string="Description", related="product_id.display_name")
    qc_id = fields.Many2one(comodel_name="mrp.workorder.qc.line", string="Order Inputan")
    product_id = fields.Many2one(comodel_name="product.product", string="Products")
    product_uom_id = fields.Many2one(
        'product.uom', 'Product Unit of Measure')
    date_start = fields.Datetime('Deadline Start', copy=False, default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self._uid)
    quantity_good = fields.Float(string="Quantity Good", digits=dp.get_precision('Product Unit of Measure'),
                                 required=True)
    quantity_reject = fields.Float(string="Quantity Reject", digits=dp.get_precision('Product Unit of Measure'),
                                   )
    quantity_sample = fields.Float(string="Quantity Sample", digits=dp.get_precision('Product Unit of Measure'),
                                   )

    product_qty = fields.Float(string="Quantity To Produce", digits=dp.get_precision('Product Unit of Measure'))
    log_ids = fields.One2many(comodel_name="workorder_qc.log.line", inverse_name="qc_id", string="Progress Record",
                              compute="_compute_log_ids")
    next_work_order_id = fields.Many2one(comodel_name="mrp.workorder",
                                         string="Next Work Order", related="qc_id.next_work_order_id")

    is_work_order_finishing = fields.Boolean(string="Check Work Order Finishing", compute="_compute_workorder_type")
    qty_produced = fields.Float(string="Qty Produced", digits=dp.get_precision('Product Unit of Measure'),

                                help="Jumlah Quantity Yand DiProduksi Dari QC GOOD dan QC REJECT"
                                     "\n Digunakan Untuk Mengecek Sisa Quantity Yang Bisa Diinput")

    @api.depends('qc_id')
    def _compute_workorder_type(self):
        self.is_work_order_finishing = not self.next_work_order_id and not self.qc_id.is_cutting

    @api.depends('qc_id', 'product_id')
    def _compute_log_ids(self):
        log_line_obj = self.env['workorder_qc.log.line']
        for rec in self:
            rec.log_ids = log_line_obj.search(
                [('qc_id', '=', rec.qc_id.id),
                 ('product_id', '=', rec.product_id.id)])

    @api.onchange('qty_produced')
    def _onchange_product_qty(self):
        for wiz in self:
            if wiz.qty_produced <= wiz.product_qty:
                wiz.quantity_good = wiz.product_qty - wiz.qty_produced

    @api.model
    def default_get(self, fields_list):
        res = super(ChangeInputanQty, self).default_get(fields_list)
        if 'qc_id' in fields_list and not res.get('qc_id') and self._context.get(
                'active_model') == 'mrp.workorder.qc.line' and self._context.get('active_id'):
            res['qc_id'] = self._context['active_id']

        if 'product_id' in fields_list and not res.get('product_qty') and res.get('qc_id'):
            res['product_id'] = self.env['mrp.workorder.qc.line'].browse(res['qc_id']).product_id.id

        if 'product_uom_id' in fields_list and not res.get('product_uom_id') and res.get('qc_id'):
            res['product_uom_id'] = self.env['mrp.workorder.qc.line'].browse(res['qc_id']).product_uom_id.id

        # if 'next_work_order_id' in fields_list and not res.get('product_qty') and res.get('qc_id'):
        #     res['next_work_order_id'] = self.env['mrp.workorder.qc.line'].browse(res['qc_id']).next_work_order_id.id

        if 'product_qty' in fields_list and not res.get('product_qty') and res.get('qc_id'):
            res['product_qty'] = self.env['mrp.workorder.qc.line'].browse(res['qc_id']).product_qty

        if 'qty_produced' in fields_list and not res.get('qty_produced') and res.get('qc_id'):
            res['qty_produced'] = self.env['mrp.workorder.qc.line'].browse(res['qc_id']).qty_produced

        return res

    @api.multi
    def action_confirm(self):
        qc_log_object = self.env['workorder_qc.log.line']
        qc_finished_object = self.env['mrp_workorder.qc_finished_move']
        qc_reject_object = self.env['mrp_workorder.qc_reject_move']
        for order in self:
            qc_log_data = {
                'product_id': order.product_id.id,
                'date_start': order.date_start,
                'quantity_good': order.quantity_good,
                'quantity_reject': order.quantity_reject,
                'quantity_sample': order.quantity_sample or 0.0,
                'user_id': order.user_id.id,
                'state_log_line': 'added',
                'qc_id': order.qc_id.id,
            }
            qc_log_id = qc_log_object.create(qc_log_data)
            if order.is_work_order_finishing and qc_log_id:
                if order.quantity_good:
                    qc_finished_object.create({
                        'product_id': order.product_id.id,
                        'product_qty': order.quantity_good + order.quantity_sample,
                        'product_uom_id': order.product_uom_id.id,
                        'qc_log_id': qc_log_id.id,
                        'qc_id': order.qc_id.id,
                    })
            if order.quantity_reject:
                qc_reject_object.create({
                    'product_id': order.product_id.id,
                    'product_qty': order.quantity_reject,
                    'product_uom_id': order.product_uom_id.id,
                    'qc_log_id': qc_log_id.id,
                    'qc_id': order.qc_id.id,
                })

            order.qc_id.qc_good += order.quantity_good
            order.qc_id.qc_reject += order.quantity_reject
            order.qc_id.qc_sample += order.quantity_sample

        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_adjustment(self):
        for order in self:
            self.env['workorder_qc.log.line'].create({
                'product_id': order.product_id.id,
                'date_start': order.date_start,
                'quantity_good': order.quantity_good,
                'quantity_reject': order.quantity_reject,
                'quantity_sample': order.quantity_sample or 0.0,
                'user_id': order.user_id.id,
                'state_log_line': 'adjustment',
                'qc_id': order.qc_id.id})
            order.qc_id.qc_good -= order.quantity_good
            order.qc_id.qc_reject -= order.quantity_reject
            order.qc_id.qc_sample -= order.quantity_sample

        return {'type': 'ir.actions.act_window_close'}



