from odoo import api, fields, models, tools


class WorkOrderViewReport(models.Model):
    _name = 'mrp_workorder.view_report'
    _description = 'View Pivot Work Order'
    _auto = False

    production_id = fields.Many2one(comodel_name="mrp.production", string="Manufacturing Order", readonly=True)
    date_order = fields.Datetime('Date', readonly=True)
    workorder_id = fields.Many2one(comodel_name="mrp.workorder", string="Work Order", readonly=True)
    product_id = fields.Many2one(comodel_name="product.product", string="Products", readonly=True)
    qty_to_produce = fields.Float(string="To Produce",  readonly=True)
    qty_good = fields.Float(string="Quantity Good", readonly=True)
    qty_reject = fields.Float(string="Quantity Reject", readonly=True)
    qty_sample = fields.Float(string="Quantity Sample", readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'mrp_workorder_view_report')
        self._cr.execute("""
            create or replace view mrp_workorder_view_report as
            (select
                min(wo.id) as id,
                wo.id as workorder_id,
                wo.production_id as production_id,
                wo.date_start as date_order,
                ql.product_id as product_id,
                coalesce(sum(ql.product_qty),0) as qty_to_produce,
                coalesce(sum(ql.qc_good),0) as qty_good,
                coalesce(sum(ql.qc_reject),0) as qty_reject,
                coalesce(sum(ql.qc_sample),0) as qty_sample
            from mrp_workorder wo
            left join mrp_production mp on (mp.id = wo.production_id)
            left join mrp_workorder_qc_line ql on (ql.workorder_id = wo.id)
            left join product_product pp on (pp.id = ql.product_id)
            where mp.state not in ('done','cancel')
            and wo.skipped = False
            and wo.state == 'progress'
            group by wo.id, wo.production_id, ql.product_id, mp.state, wo.date_start
            order by wo.production_id
            )
        """)
