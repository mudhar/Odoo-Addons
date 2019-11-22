from openerp import models, fields, api, _


class MrpProductionWizard(models.TransientModel):

    """ Remove Duplicate Line On MRP BOM"""
    _name = 'mrp_production.wizard'

    @api.multi
    def action_cancel_production(self):
        active_ids = self._context.get('active_ids')
        production_ids = self.env['mrp.production']
        procurement_ids = self.env['procurement.order']
        for production in production_ids.browse(active_ids):
            production.mapped('move_created_ids').action_cancel()
            move_line_ids = production.move_lines.mapped('id')
            procurements = procurement_ids.search([('move_dest_id', 'in', move_line_ids)])
            procurements.cancel()
            production.mapped('move_lines').action_cancel()
            procurements.write({'state': 'exception'})
            production.write({'state': 'cancel'})
        return {'type': 'ir.actions.act_window_close'}





