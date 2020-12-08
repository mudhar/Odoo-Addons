# -*- coding: utf-8 -*-
from odoo import api, models


class AssemblyPlanCostReport(models.Model):
    _name = 'report.textile_assembly.assembly_plan_cost_report'

    @api.multi
    def get_lines(self, plans):
        product_lines = []
        for plan in plans:
            product = plan.product_template_id.name
            # attribute_set = plan.produce_ids.mapped('id')
            for produce in plan.produce_ids:
                if produce.attribute_id and produce.quantity_actual:
                    product_line = {
                        'plan': plan.name,
                        'attribs': produce.attribute_id.name,
                        'quantity_to_produce': produce.quantity_actual,
                        'currency': plan.currency_id,
                        'name': product,
                        'variant_lines': [],
                        'raw_lines': [],
                        'cmt_lines': [],
                        'service_lines': [],
                        'total': 0.0,
                        'unit_cost': 0.0,
                    }
                    for variant in plan.plan_line_actual_ids.filtered(
                            lambda x: (x.attribute_value_ids[0] in produce.attribute_id)
                            or (x.attribute_value_ids[1] in produce.attribute_id)):
                        set_product_variant = {
                            'attribute_value_ids': variant.attribute_value_ids,
                            'quantity_actual': variant.actual_quantity,
                        }
                        product_line['variant_lines'] += [set_product_variant]

                    # Tabel Raw Material
                    total_raw = 0.0
                    for raw in plan.raw_line_ids:
                        if raw.product_id and raw.attribute_id[0].id != produce.attribute_id.id:
                            continue
                        if raw.product_id and raw.attribute_id[0].id == produce.attribute_id.id:
                            data_raw_material = {
                                'product_id': raw.product_id,
                                'product_qty': raw.qty_to_actual,
                                'product_uom_id': raw.product_uom_id,
                                'price_unit': raw.price_unit,
                                'price_subtotal': raw.qty_to_actual * raw.price_unit,
                            }
                            total_raw += data_raw_material['price_subtotal']
                            product_line['raw_lines'] += [data_raw_material]

                    # Tabel CMT

                    total_cmt_attributes = 0.0
                    for cmt in plan.cmt_material_line_ids.filtered(lambda x: x.product_id.attribute_value_ids):
                        if product_line['variant_lines']:
                            for attrib in product_line['variant_lines']:
                                if (attrib.get('attribute_value_ids')[0] in cmt.product_id.attribute_value_ids)\
                                        or (attrib.get('attribute_value_ids')[1] in cmt.product_id.attribute_value_ids):
                                    data_cmt_material = {
                                        'product_id': cmt.product_id,
                                        'product_qty': attrib['quantity_actual'],
                                        'product_uom_id': cmt.product_uom_id,
                                        'price_unit': cmt.price_unit,
                                        'price_subtotal': attrib['quantity_actual'] * cmt.price_unit,
                                    }
                                    total_cmt_attributes += data_cmt_material['price_subtotal']
                                    product_line['cmt_lines'] += [data_cmt_material]

                    total_cmt_non_attributes = 0.0
                    for cmt in plan.cmt_material_line_ids.filtered(
                            lambda x: not x.product_id.attribute_value_ids):
                        if cmt.product_id:
                            data_cmt_material = {
                                'product_id': cmt.product_id,
                                'product_qty': cmt.product_qty * produce.quantity_actual,
                                'product_uom_id': cmt.product_uom_id,
                                'price_unit': cmt.price_unit,
                                'price_subtotal': (cmt.product_qty * produce.quantity_actual) * cmt.price_unit,
                            }
                            total_cmt_non_attributes += data_cmt_material['price_subtotal']
                            product_line['cmt_lines'] += [data_cmt_material]

                    # Tabel Biaya Produksi
                    total_service = 0.0
                    for service in plan.cmt_service_ids:
                        if service.product_id:
                            data_services = {
                                'product_id': service.product_id,
                                'product_qty': service.product_qty * produce.quantity_actual,
                                'product_uom_id': service.product_uom_id,
                                'price_unit': service.price_unit,
                                'price_subtotal': (service.product_qty * produce.quantity_actual) * service.price_unit,
                            }
                            total_service += data_services['price_subtotal']
                            product_line['service_lines'] += [data_services]

                    product_line['total'] = total_raw + total_cmt_attributes + total_cmt_non_attributes + total_service
                    product_line['unit_cost'] = product_line['total'] / product_line['quantity_to_produce']
                    product_lines += [product_line]

        return product_lines

    @api.model
    def get_report_values(self, docids, data=None):
        plans = self.env['assembly.plan'].browse(docids)
        res = self.get_lines(plans)
        return {'lines': res}
