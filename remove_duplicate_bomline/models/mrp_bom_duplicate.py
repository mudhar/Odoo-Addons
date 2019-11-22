from openerp import models, fields, api, _


class MrpBomDuplicate(models.TransientModel):

    """ Remove Duplicate Line On MRP BOM"""
    _name = 'mrpbom.duplicate.wizard'

    @api.multi
    def action_remove_duplicate(self):
        active_ids = self._context.get('active_ids')
        bom_ids = self.env['mrp.bom']
        for bom in bom_ids.browse(active_ids):
            for line in bom.bom_line_ids:
                lines = self.env['mrp.bom.line'].search_count(
                    [('product_id', '=', line.product_id.id),
                     ('bom_id', '=', line.bom_id.id)])
                if lines > 1:
                    line.unlink()
        return {'type': 'ir.actions.act_window_close'}





