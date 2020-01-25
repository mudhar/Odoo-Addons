from odoo import api, models, _
from odoo.exceptions import UserError


class AssemblyProductionCostReport(models.Model):
    _name = 'report.textile_assembly.assembly_production_cost_report'

    @api.multi
    def get_lines(self, assemblies):
        product_lines = []
        for assembly in assemblies:
            product = assembly.product_tmpl_id.name
            attribute_set = assembly.raw_material_line_ids.mapped('attribute_id')
            for attrib in attribute_set:
                if attrib.id:
                    product_line = {
                        'assembly': assembly.name,
                        'pattern_code': assembly.pattern_code,
                        'image': assembly.product_image,
                        'routing_id': assembly.routing_id.name,
                        'currency': assembly.currency_id,
                        'name': product,
                        'attributes': attrib.name,
                        'variant_lines': [],
                        'raw_lines': [],
                        'cmt_lines': [],
                        'service_lines': [],
                        'total': 0.0,
                    }

                    # list component ratio
                    set_attribute_variants = assembly.variant_line_ids.filtered(
                        lambda x: x.attribute_value_ids[0] in attrib or x.attribute_value_ids[1] in attrib)

                    for variant in assembly.variant_line_ids.filtered(
                        lambda x: x.attribute_value_ids[0] in attrib or x.attribute_value_ids[1] in attrib):
                        variants = {
                            'product_id': variant.product_id,
                            'ratio': variant.ratio,
                        }
                        product_line['variant_lines'] += [variants]

                    for variant in assembly.variant_line_ids:
                        if variant.product_id and (
                                variant.attribute_value_ids[0].id != attrib.id
                                or variant.attribute_value_ids[1].id != attrib.id):
                            continue
                        if variant.product_id and (
                                variant.attribute_value_ids[0].id == attrib.id
                                or variant.attribute_value_ids[1].id != attrib.id):
                            variants = {
                                'product_id': variant.product_id,
                                # 'attribs': [(''.join('%s\t' % value.name for value in variant.attribute_value_ids))],
                                'ratio': variant.ratio
                            }
                            product_line['variant_lines'] += [variants]

                    # list raw material
                    total_raw = 0.0
                    for raw in assembly.raw_material_line_ids:
                        if raw.product_id and raw.attribute_id.id != attrib.id:
                            continue

                        if raw.product_id and raw.attribute_id.id == attrib.id:
                            raws = {
                                'product_id': raw.product_id,
                                'attribs': raw.attribute_id,
                                'product_qty':raw.product_qty,
                                'product_uom_id': raw.product_uom_id,
                                'price_unit': raw.price_unit,
                                'price_subtotal': raw.price_subtotal,
                            }
                            total_raw += raws['price_subtotal']
                            product_line['raw_lines'] += [raws]

                    total_cmt = 0.0
                    # list cmt
                    for cmt in assembly.cmt_template_ids:
                        if cmt.product_id:
                            cmts = {
                                'product_id': cmt.product_id,
                                'product_qty': cmt.product_qty,
                                'product_uom_id': cmt.product_uom_id,
                                'price_unit': cmt.price_unit,
                                'price_subtotal': cmt.price_subtotal,
                            }
                            total_cmt += cmts['price_subtotal']
                            product_line['cmt_lines'] += [cmts]

                    total_service = 0.0
                    # list product services
                    for service in assembly.cmt_service_ids:
                        if service.product_id:
                            services = {
                                'product_id': service.product_id,
                                'product_qty': service.product_qty,
                                'product_uom_id': service.product_uom_id,
                                'price_unit': service.price_unit,
                                'price_subtotal': service.price_subtotal,
                            }
                            total_service += services['price_subtotal']
                            product_line['service_lines'] += [services]

                    product_line['total'] = total_raw + total_cmt + total_service
                    product_lines += [product_line]

        return product_lines

    @api.model
    def get_report_values(self, docids, data=None):
        assemblies = self.env['assembly.production'].browse(docids)
        res = self.get_lines(assemblies)
        return {'lines': res}





