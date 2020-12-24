# -*- coding: utf-8 -*-
from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    assembly_plan_id = fields.Many2one(comodel_name="assembly.plan",
                                       string="Assembly Plan Order")
    work_order_id = fields.Many2one(comodel_name="mrp.workorder", string="PO Created From Work Order")

    @api.multi
    def unlink(self):
        result = super(PurchaseOrder, self).unlink()
        if self.work_order_id or self.assembly_plan_id:
            for inv in self.invoice_ids:
                if inv.state in ('draft', 'cancel'):
                    inv.unlink()
        return result

    @api.multi
    def button_approve(self, force=False):
        result = super(PurchaseOrder, self).button_approve(force=False)
        for order in self:
            if order.assembly_plan_id:
                cmt_material_ids = self.env['assembly.plan.cmt.material'].search(
                    [('plan_id', '=', order.assembly_plan_id.id)])
                raw_material_ids = self.env['assembly.plan.raw.material'].search(
                    [('plan_id', '=', order.assembly_plan_id.id)])
                for line in order.order_line:
                    if cmt_material_ids and line.product_id in cmt_material_ids.mapped('product_id'):
                        for cmt in cmt_material_ids.filtered(lambda x: x.product_id.id == line.product_id.id):
                            cmt_price = line.product_uom._compute_price(line.price_unit, line.product_id.uom_id)
                            cmt.write({'price_unit': cmt_price})
                    if raw_material_ids and line.product_id in raw_material_ids.mapped('product_id'):
                        for raw in raw_material_ids.filtered(lambda x: x.product_id.id == line.product_id.id):
                            raw_price = line.product_uom._compute_price(line.price_unit, line.product_id.uom_id)
                            raw.write({'price_unit': raw_price})

        return result


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_qty')
    def onchange_product_qty_assembly(self):
        for order in self:
            plan_id = order.order_id.assembly_plan_id
            if order.product_id and plan_id:
                cmt_material_ids = self.env['assembly.plan.cmt.material'].search([('plan_id', '=', plan_id.id)])
                if cmt_material_ids and order.product_id in cmt_material_ids.mapped('product_id'):
                    for cmt in cmt_material_ids.filtered(lambda x: x.product_id.id == order.product_id.id):
                        cmt_price_unit = order.product_id.uom_id._compute_price(cmt.price_unit, order.product_uom)
                        order.update({'price_unit': cmt_price_unit})

                raw_material_ids = self.env['assembly.plan.raw.material'].search(
                    [('plan_id', '=', plan_id.id)])
                if raw_material_ids and order.product_id in raw_material_ids.mapped('product_id'):
                    for raw in raw_material_ids.filtered(lambda x: x.product_id.id == order.product_id.id):
                        raw_price_unit = order.product_id.uom_id._compute_price(raw.price_unit, order.product_uom)
                        order.update({'price_unit': raw_price_unit})
        return {}
