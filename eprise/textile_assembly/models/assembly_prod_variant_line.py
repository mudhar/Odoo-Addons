from odoo import api, fields, models


class AssemblyProdVariantLine(models.Model):
    _name = 'assembly.prod.variant.line'
    _rec_name = 'product_id'
    _description = 'Assembly Variant Line'
    _order = 'assembly_id, sequence, id'

    assembly_id = fields.Many2one(comodel_name="assembly.production", string="Variant Line",
                                  ondelete='cascade', index=True)
    sequence = fields.Integer(string='Sequence', default=1)

    product_id = fields.Many2one(comodel_name="product.product",
                                 string="Products", store=True)
    attribute_value_ids = fields.Many2many('product.attribute.value', string="Variants", index=True)
    ratio = fields.Float(string="Ratio", default=0.0, store=True)
    state = fields.Selection(related="assembly_id.state", store=True)

    # create Data assembly.plan.line
    @api.multi
    def prepare_assembly_plan_line(self, product):
        # (6, _, ids)
        # replaces all existing records
        # in the set by the ids list,
        # equivalent to using the command 5 followed by a command 4 for each id in ids.

        self.ensure_one()
        res = {
            'product_variant_id': product,
            'ratio': self.ratio,
            'sequence': self.sequence,
            'attribute_value_ids': [(6, 0, self.attribute_value_ids.ids)]

        }
        return res

    @api.multi
    def assembly_plan_line_create(self, plan_id, product):
        plan_lines = self.env['assembly.plan.line']
        for line in self:
            vals = line.prepare_assembly_plan_line(product=product)
            vals.update({'plan_id': plan_id,
                         'plan_line_ids': [(6, 0, [line.id])]})
            plan_lines |= self.env['assembly.plan.line'].create(vals)
        return plan_lines