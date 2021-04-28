from odoo import fields, models


class PickingBarcodeAction(models.TransientModel):
    """
    get default value to find picking on picking model
    """
    _name = "picking.barcode.action"
    _inherit = "barcodes.barcode_events_mixin"
    _description = "Picking Barcode Action"

    model = fields.Char(required=True, readonly=True)
    domain = fields.Char()
    method = fields.Char(required=True, readonly=True)
    state = fields.Selection(
        [("waiting", "Waiting"), ("warning", "Warning")],
        default="waiting",
        readonly=True,
    )
    status = fields.Text(readonly=True, default="Start scanning")

    def button_test_find(self):
        """
        parsing variable to test method find barcode
        :return: list
        """
        barcode = 'READY OUT'
        pickings = self.env['stock.picking'].find_picking_by_barcode(barcode)
        return pickings
