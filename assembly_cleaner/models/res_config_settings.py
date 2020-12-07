# -*- coding: utf-8 -*-

from odoo import models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.multi
    def remove_assembly(self):
        to_removes = [
            # keys model
            ['assembly.plan', ],
            ['assembly.plan.cmt.material', ],
            ['assembly.plan.line', ],
            ['assembly.plan.produce', ],
            ['assembly.plan.raw.material', ],
            ['assembly.plan.services', ],
            ['assembly.prod.variant.line', ],
            ['assembly.production', ],
            ['assembly.raw.material.line', ],
            ['mrp.production.variant', ],
            ['mrp_workorder.qc_finished_move', ],
            ['mrp_workorder.qc_reject_move', ],
            ['mrp.workorder.qc.line', ],
            ['mrp.workorder.service.line', ],
            ['workorder_qc.log.line', ],

        ]
        try:
            for line in to_removes:
                obj_name = line[0]
                obj = self.pool.get(obj_name)
                if obj:
                    sql = "delete from %s" % obj._table
                    self._cr.execute(sql)
        except Exception as e:
            pass
        return True

    @api.multi
    def reset_number_seq(self):
        try:
            seqs = self.env['ir.sequence'].search([
                '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|',
                ('code', '=', 'assembly.plan'),
                ('code', '=', 'stock.picking.materials_incoming'),
                ('code', '=', 'stock.picking.return_cmt'),
                ('code', '=', 'stock.picking.return_non_cmt'),
                ('code', '=', 'stock.picking.materials_outgoing'),
                ('code', '=', 'stock.picking.goods_incoming'),
                ('code', '=', 'stock.picking.goods_outgoing'),
                ('code', '=', 'stock.picking.return_customer'),
                ('code', '=', 'picking.internal.store.wh'),
                ('code', '=', 'picking.internal.wh.store'),
                ('code', '=', 'picking.internal.store.store'),
                ('code', '=', 'purchase.order.materials'),
                ('code', '=', 'purchase.order.goods'),
                ('code', '=', 'purchase.order.subpo'),
            ])
            if seqs:
                seqs.write({'number_next': 1,
                            'number_next_actual': 1})
                date_range = seqs.filtered(lambda seq: seq.date_range_ids)
                date_range.mapped('date_range_ids').unlink()
        except Exception as e:
            pass
        return True
