import calendar
from datetime import datetime
from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def create(self, vals):
        sequence_object = self.env['ir.sequence']
        if vals.get('product_select_type', 'materials') == 'materials':
            sequence_id = sequence_object.search([('code', '=', 'purchase.order.materials')])
            if sequence_id.use_date_range and vals.get('date_order'):
                # 2020-01-10
                date_to = fields.Date.from_string(vals.get('date_order'))
                year = date_to.year
                month = date_to.month
                days = calendar.monthrange(year, month)

                # date_range = sequence_id.date_range_ids.filtered(
                #     lambda dt: dt.date_from <= date_to.strftime('%Y-%m-%d') <= dt.date_to)
                date_to_string = date_to.strftime('%Y-%m-%d')
                date_range = self.env['ir.sequence.date_range'].search(
                    [('sequence_id', '=', sequence_id.id), ('date_from', '<=', date_to_string),
                     ('date_to', '>=', date_to_string)], order='date_to desc', limit=1)
                if not date_range:
                    dt_from = '{}-{}-01'.format(year, month)
                    dt_to = '{}-{}-{}'.format(year, month, days[1])
                    seq_date = self.env['ir.sequence.date_range'].create({
                        'sequence_id': sequence_id.id,
                        'date_from': dt_from,
                        'date_to': dt_to
                    })
                    seq_prefix = self.env['assembly.plan']._create_sequence_prefix(sequence_id, seq_date)
                    vals['name'] = seq_prefix
                else:
                    seq_prefix = self.env['assembly.plan']._create_sequence_prefix(sequence_id, date_range)
                    vals['name'] = seq_prefix

        return super(PurchaseOrder, self).create(vals)


