from openerp import models, fields, api, _
from openerp.addons import decimal_precision as dp


class MrpProductionWorkcenterLine(models.Model):
    _inherit = 'mrp.production.workcenter.line'

    note_desc = fields.Text(string="Description", readonly=True,)
    note_pending = fields.Text(string="Reason", readonly=True)


class MrpRequestProduct(models.Model):
    _name = 'mrp.request.product'
    _rec_name = 'name'
    _description = 'MRP Request Product'

    name = fields.Char('Reference', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    user_id = fields.Many2one(comodel_name="res.users", string="Request By",  default=lambda self: self._uid)
    req_date = fields.Datetime(string="Request Date", default=fields.datetime.now(), copy=False, index=True, required=True)
    line_ids = fields.One2many(comodel_name="mrp.request.product.line", inverse_name="request_id",
                               string="Lines", copy=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('to approve', 'To Approve'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')
    reject_reason_id = fields.Text(string="Reject Reason", readonly=True)

    @api.model
    def create(self, values):
        if values.get('name', _('New')) == _('New'):
            values['name'] = self.env['ir.sequence'].next_by_code('mrp.request.product') or _('New')
        return super(MrpRequestProduct, self).create(values)

    @api.multi
    def button_confirm(self):
        for order in self:
            if order.state == 'to approve' and order.user_has_groups('stock.group_stock_user'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
        return True

    @api.multi
    def button_approve(self):
        self.write({'state': 'approve'})
        return True

    @api.multi
    def button_reject(self):
        self.write({'state': 'reject'})
        return True


class MrpRequestProductLine(models.Model):
    _name = 'mrp.request.product.line'
    _rec_name = 'product_id'
    _description = 'MRP Request Product Line'

    product_id = fields.Many2one(comodel_name="product.product", string="Products",
                                 domain="[('type', 'not in', ['service', 'consu']), ('purchase_ok', '=', True)]",
                                 required=True)
    product_qty = fields.Float('Required Quantity', digits_compute=dp.get_precision('Product Unit of Measure'),
                               required=True)
    product_uom = fields.Many2one('product.uom', 'Product Unit of Measure')

    request_id = fields.Many2one(comodel_name="mrp.request.product", string="Request ID", select=True)
    req_state = fields.Selection("Request State", related='request_id.state')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id


class MrpBom(models.Model):

    _inherit = 'mrp.bom'

    @api.multi
    def _prepare_wc_line(self, wc_use, level=0, factor=1):
        res = super(MrpBom, self)._prepare_wc_line(wc_use, level=0, factor=1)
        res.update(
            {
                'note_desc': wc_use.note,

            })

        return res

    @api.model
    def _prepare_ppic_line(self, bom_line, quantity, factor=1):
        res = super(MrpBom, self)._prepare_ppic_line(bom_line, quantity, factor=1)
        res.update({
            'sequence': bom_line.sequence,
            'note_bom': bom_line.note_bom
        })
        return res


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    note_bom = fields.Char(string="Note")


class MrpProductionPpicLine(models.Model):
    _inherit = 'mrp.production.ppic.line'

    sequence = fields.Integer(string="Sequence")
    note_bom = fields.Char(string="Note")



