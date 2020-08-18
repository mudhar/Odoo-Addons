from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools.translate import _


class AssemblyProdVariantLine(models.Model):
    _name = 'assembly.prod.variant.line'
    _rec_name = 'product_id'
    _description = 'Assembly Variant Line'
    _order = 'product_id, sequence, attribute_value_ids'

    assembly_id = fields.Many2one(comodel_name="assembly.production", string="Assembly Order",
                                  ondelete='cascade', index=True)
    sequence = fields.Integer(string='Seq', default=1)
    product_id = fields.Many2one(comodel_name="product.product",
                                 string="Products", required=True)
    product_uom_id = fields.Many2one(
        'product.uom', 'UoM', readonly=True, related="product_id.uom_id")
    attribute_value_ids = fields.Many2many('product.attribute.value', string="Attributes",
                                           related="product_id.attribute_value_ids")
    ratio = fields.Float(string="Of Ratio",  digits=dp.get_precision('Product Unit of Measure'))
    state = fields.Selection(related="assembly_id.state", string="State Production")
    product_template_id = fields.Many2one(comodel_name="product.template", related="assembly_id.product_tmpl_id",
                                          string="Template Product")

    @api.constrains('product_id')
    def _check_duplicate_product(self):
        variant_ids = self.env['assembly.prod.variant.line'].search_count(
            [('product_id', '=', self.product_id.id), ('assembly_id', '=', self.assembly_id.id)])
        if variant_ids and variant_ids > 1:
            raise UserError(_("Duplicate Product %s Total Duplicate %s") % (self.product_id.display_name, str(variant_ids)))
        else:
            return False

    @api.multi
    @api.onchange('product_id')
    def _onchange_product_id(self):
        values = {}
        domain = {'product_id': [('product_tmpl_id', '=', self.product_template_id.id)]}
        result = {'domain': domain}
        return result

    def generate_assembly_plan_line(self, plan_id):
        plan_variants = self.env['assembly.plan.line']
        done = self.env['assembly.plan.line'].browse()
        for line in self:
            for val in line.prepare_assembly_plan_line(plan_id):
                done += plan_variants.create(val)
        return done

    # create Data assembly.plan.line
    @api.multi
    def prepare_assembly_plan_line(self, plan_id):
        # (6, _, ids)
        # replaces all existing records
        # in the set by the ids list,
        # equivalent to using the command 5 followed by a command 4 for each id in ids.

        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        values = {
            'plan_id': plan_id.id,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom_id.id,
            'ratio': self.ratio,
            'sequence': self.sequence,
            'attribute_value_ids': [(6, 0, self.attribute_value_ids.ids)]
        }
        res.append(values)
        return res
