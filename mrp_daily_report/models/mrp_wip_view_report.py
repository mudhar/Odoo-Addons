# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools


class WipViewReport(models.Model):
    _name = "mrp_wip.view_report"
    _description = "View Pivot Work In Process"
    _auto = False

    product_id = fields.Many2one(comodel_name="product.product", string="Products", readonly=True)
    production_id = fields.Many2one(comodel_name="mrp.production", string="Manufactring Order", readonly=True)

    qty_used = fields.Float(string="Quantity Used", readonly=True)
    qty_reject = fields.Float(string="Quantity Reject", readonly=True)
    qty_differ = fields.Float(string="Quantity Differ", readonly=True)
    qty_return = fields.Float(string="Quantity Return", readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'mrp_wip_view_report')
        self._cr.execute("""
        create or replace view mrp_wip_view_report as (
        select
            min(sml.id)as id,
            sml.product_id as product_id,
            sm.raw_material_production_id as production_id,
            coalesce(sum(sml.qty_done),0.0)as qty_used,
            0.0 qty_reject,
            0.0 qty_differ,
            0.0 qty_return
        from stock_move_line sml
        left join product_product pp on (pp.id = sml.product_id)
        left join stock_move sm on (sm.id = sml.move_id)
        left join mrp_production mp on (mp.id = sm.raw_material_production_id)
        where mp.state not in ('done', 'cancel')
        and not sm.scrapped
        and not sm.returned_picking
        group by sml.product_id, mp.state, sm.raw_material_production_id
        union all
        select
            min(sml.id)as id,
            sml.product_id as product_id,
            sm.raw_material_production_id as production_id,
            0.0 qty_used,
            coalesce(sum(sml.qty_done),0.0)as qty_reject,
            0.0 qty_differ,
            0.0 qty_return
        from stock_move_line sml
        left join product_product pp on (pp.id = sml.product_id)
        left join stock_move sm on (sm.id = sml.move_id)
        left join mrp_production mp on (mp.id = sm.raw_material_production_id)
        where mp.state not in ('done', 'cancel')
        and sm.scrapped
        and not sm.returned_picking
        group by sml.product_id, mp.state, sm.raw_material_production_id
        union all
        select
            min(sml.id)as id,
            sml.product_id as product_id,
            sm.raw_material_production_id as production_id,
            0.0 qty_used,
            0.0 qty_reject,
            (case when sum(sm.product_uom_qty) < sum(sml.qty_done) 
             then sum(sml.qty_done) - sum(sm.product_uom_qty)
            else 0.0
            end)as qty_differ,
            0.0 qty_return
        from stock_move_line sml
        left join product_product pp on (pp.id = sml.product_id)
        left join stock_move sm on (sm.id = sml.move_id)
        left join mrp_production mp on (mp.id = sm.raw_material_production_id)
        where mp.state not in ('done', 'cancel')
        and not sm.scrapped
        and not sm.returned_picking
        group by sml.product_id, mp.state, sm.raw_material_production_id
        union all
        select
            min(sml.id)as id,
            sml.product_id as product_id,
            sm.raw_material_production_id as production_id,
            0.0 qty_used,
            0.0 qty_reject,
            0.0 qty_differ,
            coalesce(sum(sml.qty_done),0.0)as qty_return
        from stock_move_line sml
        left join product_product pp on (pp.id = sml.product_id)
        left join stock_move sm on (sm.id = sml.move_id)
        left join mrp_production mp on (mp.id = sm.raw_material_production_id)
        where mp.state not in ('done', 'cancel')
        and not sm.scrapped
        and sm.returned_picking
        group by sml.product_id, mp.state, sm.raw_material_production_id
         )""")


