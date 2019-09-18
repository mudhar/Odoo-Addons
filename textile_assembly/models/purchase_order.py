# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    assembly_plan_id = fields.Many2one(comodel_name="assembly.plan",
                                       string="Assembly Plan Order")
    work_order_id = fields.Many2one(comodel_name="mrp.workorder", string="PO Created From Work Order")

    @api.multi
    def button_approve(self, force=False):
        result = super(PurchaseOrder, self).button_approve(force=False)
        for order in self:
            if order.assembly_plan_id:
                for line in order.order_line:
                    if line.product_id and line.price_unit:
                        order.update_price_unit_assembly(order.assembly_plan_id, line.product_id, line.price_unit)
                        for raw in self.env['assembly.plan.raw.material'].search(
                                [('plan_id', '=', order.assembly_plan_id.id)]).filtered(
                            lambda x: x.product_id.id == line.product_id.id
                                    and x.price_unit != line.price_unit):
                            raw.write({'price_unit': line.price_unit})
                        for cmt in self.env['assembly.plan.cmt.material'].search(
                                [('plan_id', '=', order.assembly_plan_id.id)]).filtered(
                            lambda x: x.product_id.id == line.product_id.id
                                    and x.price_unit != line.price_unit):
                            cmt.write({'price_unit': line.price_unit})

        return result

    @api.multi
    def update_price_unit_assembly(self, assembly_plan_id, product_id, price_unit):
        assembly_id = self.env['assembly.plan'].search([('id', '=', assembly_plan_id.id)]).mapped('assembly_id')
        if assembly_id:
            for raw in self.env['assembly.raw.material.line'].search(
                    [('assembly_id', '=', assembly_id.id)]).filtered(lambda x: x.product_id.id == product_id.id and x.price_unit != price_unit):
                raw.write({'price_unit': price_unit})
            for cmt in self.env['assembly.cmt.material.line'].search(
                    [('assembly_id', '=', assembly_id.id)]).filtered(lambda x: x.product_id.id == product_id.id and x.price_unit != price_unit):
                cmt.write({'price_unit': price_unit})
        return {}


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_qty')
    def onchange_product_qty_assembly(self):
        for order in self:
            plan_id = order.order_id.assembly_plan_id
            if plan_id:
                for cmt in self.env['assembly.plan.cmt.material'].search([('plan_id', '=', plan_id.id)]):
                    if cmt.product_id.id != order.product_id.id:
                        continue
                    if cmt.product_id.id == order.product_id.id:
                        order.price_unit = cmt.price_unit

                for raw in self.env['assembly.plan.raw.material'].search([('plan_id', '=', plan_id.id)]):
                    if raw.product_id.id != order.product_id.id:
                        continue
                    if raw.product_id.id == order.product_id.id:
                        order.price_unit = raw.price_unit
        return {}





