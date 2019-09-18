from odoo import api, models


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    @api.onchange('workcenter_id')
    def _select_workcenter_id(self):
        self.update({'name': self.workcenter_id.name})


class MrpRouting(models.Model):
    _inherit = 'mrp.routing'

    @api.model
    def create(self, vals):
        if vals.get('operation_ids'):
            for index, operation in enumerate(vals['operation_ids']):
                if len(operation) == 3 and operation[0] == 0:
                    operation[2]['sequence'] = index + 1
        result = super(MrpRouting, self).create(vals)
        return result

    @api.multi
    def write(self, vals):
        """
        Kalau Ada Value Baru Di Reset Lagi Sequencenya
        :param vals:
        :return:
        """
        if vals.get('operation_ids'):
            for index, operation in enumerate(vals['operation_ids']):
                if len(operation) == 3 and operation[0] == 0:
                    operation[2]['sequence'] = index + 1
        result = super(MrpRouting, self).write(vals)
        return result




