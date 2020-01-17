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

    # @api.model_cr
    # def init(self):
    #     tools.drop_view_if_exists(self._cr, 'mrp_daily_report')
    #     self._cr.execute("""
    #         create or replace view mrp_daily_report as (
    #         with product_consume as
    #         (select
    #             min(cmt.id) as id,
    #             cmt.plan_id,
    #             plan.date_planned_start as date_order,
    #             plan.name as name,
    #             cmt.product_id as product_id,
    #             pwl.workorder_id as workorder_id,
    #             coalesce(sum(pwl.qty_good),0) as qty_good,
    #             coalesce(sum(cmt.quantity_to_actual),0) as qty_consume,
    #             coalesce(sum(cmt.qty_consumed),0) as qty_consumed,
    #             coalesce(sum(cmt.qty_used),0)as qty_used,
    #             coalesce(sum(cmt.qty_reject),0) as qty_reject,
    #             coalesce(sum(cmt.qty_return),0) as qty_return,
    #             coalesce(sum(cmt.qty_differ),0) as qty_differ
    #         from assembly_plan plan
    #         left join assembly_plan_cmt_material cmt on (cmt.plan_id=plan.id)
    #         left join product_product pp on (pp.id=cmt.product_id)
    #         left join plan_workorders_line pwl on (pwl.plan_id=plan.id)
    #         left join mrp_workorder wo on (wo.id=pwl.workorder_id)
    #         group by plan.name, cmt.plan_id, cmt.product_id, pwl.workorder_id,plan.state,plan.date_planned_start
    #         having plan.state in ('done','cancel')
    #         union all
    #         select
    #             min(-raw.id) as id,
    #             raw.plan_id,
    #             plan.date_planned_start as date_order,
    #             plan.name as name,
    #             raw.product_id as product_id,
    #             pwl.workorder_id as workorder_id,
    #             coalesce(sum(pwl.qty_good),0) as qty_good,
    #             coalesce(sum(raw.qty_to_actual),0) as qty_consume,
    #             coalesce(sum(raw.qty_consumed),0) as qty_consumed,
    #             coalesce(sum(raw.qty_used),0)as qty_used,
    #             coalesce(sum(raw.qty_reject),0) as qty_reject,
    #             coalesce(sum(raw.qty_return),0) as qty_return,
    #             coalesce(sum(raw.qty_differ),0) as qty_differ
    #         from assembly_plan plan
    #         left join assembly_plan_raw_material raw on (raw.plan_id=plan.id)
    #         left join product_product pp on (pp.id=raw.product_id)
    #         left join plan_workorders_line pwl on (pwl.plan_id=plan.id)
    #         left join mrp_workorder wo on (wo.id=pwl.workorder_id)
    #         group by plan.name, raw.plan_id, raw.product_id, pwl.workorder_id,plan.state,plan.date_planned_start
    #         having plan.state in ('done','cancel')),
    #     product_produce as
    #         (select
    #             min(variant.id) as id,
    #             variant.plan_id,
    #             sum(variant.actual_quantity) as qty_produce,
    #             sum(variant.qty_sample) as qty_sample,
    #             sum(variant.qty_produced) as qty_produced
    #         from assembly_plan_line variant
    #         left join assembly_plan plan on (plan.id=variant.plan_id)
    #         group by variant.plan_id, plan.state
    #         having plan.state in ('done', 'cancel'))
    #
    #     select
    #         min(pc.id) as id,
    #         pc.date_order as date_order,
    #         pc.name as name,
    #         pc.workorder_id as workorder_id,
    #         sum(pc.qty_good) as qty_good,
    #         count(pc.*)as nbr,
    #         variant.qty_produce,
    #         variant.qty_sample,
    #         variant.qty_produced,
    #         pc.product_id as product_id,
    #         sum(pc.qty_consume) as qty_consume,
    #         sum(pc.qty_consumed) as qty_consumed,
    #         sum(pc.qty_used) as qty_used,
    #         sum(pc.qty_reject) as qty_reject,
    #         sum(pc.qty_return) as qty_return,
    #         sum(pc.qty_differ) as qty_differ
    #     from product_consume pc
    #     left join product_produce variant on (variant.plan_id=pc.plan_id)
    #     group by
    #     pc.date_order,
    #     pc.name,
    #     pc.workorder_id,
    #     variant.qty_produce,
    #     variant.qty_sample,
    #     variant.qty_produced,
    #     pc.product_id
    #         )""")

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


