from odoo import api, models


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
                    for variant in assembly.variant_line_ids.filtered(
                            lambda x: x.attribute_value_ids[0] in attrib or x.attribute_value_ids[1] in attrib):
                        variants = {
                            'product_id': variant.product_id,
                            'ratio': variant.ratio,
                        }
                        product_line['variant_lines'] += [variants]

                    # list raw material
                    total_raw = 0.0
                    for raw in assembly.raw_material_line_ids.filtered(lambda x: x.attribute_id.id == attrib.id):
                        data_raw_materials = {
                            'product_id': raw.product_id,
                            'attribs': raw.attribute_id,
                            'product_qty': raw.product_qty,
                            'product_uom_id': raw.product_uom_id,
                            'price_unit': raw.price_unit,
                            'price_subtotal': raw.price_subtotal,
                        }
                        total_raw += data_raw_materials['price_subtotal']
                        product_line['raw_lines'] += [data_raw_materials]

                    total_cmt = 0.0
                    # list cmt
                    for cmt in assembly.cmt_template_ids:
                        if cmt.product_id:
                            data_cmt_materials = {
                                'product_id': cmt.product_id,
                                'product_qty': cmt.product_qty,
                                'product_uom_id': cmt.product_uom_id,
                                'price_unit': cmt.price_unit,
                                'price_subtotal': cmt.price_subtotal,
                            }
                            total_cmt += data_cmt_materials['price_subtotal']
                            product_line['cmt_lines'] += [data_cmt_materials]

                    total_service = 0.0
                    # list product services
                    for service in assembly.cmt_service_ids:
                        if service.product_id:
                            data_services = {
                                'product_id': service.product_id,
                                'product_qty': service.product_qty,
                                'product_uom_id': service.product_uom_id,
                                'price_unit': service.price_unit,
                                'price_subtotal': service.price_subtotal,
                            }
                            total_service += data_services['price_subtotal']
                            product_line['service_lines'] += [data_services]

                    product_line['total'] = total_raw + total_cmt + total_service
                    product_lines += [product_line]

        return product_lines

    @api.model
    def get_report_values(self, docids, data=None):
        assemblies = self.env['assembly.production'].browse(docids)
        res = self.get_lines(assemblies)
        return {'lines': res}





