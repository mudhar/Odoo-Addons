from openerp import models, fields, api, _


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.one
    @api.depends('product_uom',
                 'product_uom.category_id',
                 'product_uom.category_id.name')
    def _compute_product_uom(self):
        if self.product_uom.category_id.name.lower() == 'surface':
            uom_name = self.product_uom.name.lower()
            if uom_name.endswith('sq'):
                self.product_type_uom = 'Roll'
            elif uom_name.startswith('sheet'):
                self.product_type_uom = 'Sheet'
        else:
            return None

    product_type_uom = fields.Char(string="Jenis Produk", compute="_compute_product_uom",
                                   help="Teknikal View Untuk Di Report Membedakan Yang Roll Dan Sheet")

