# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Textile Assembly Production',
    'version' : '11.0.1',
    'author' : 'odoo-consultants',
    'summary': 'Textile Assembly Production',
    'description': """
Textile Assembly Production\n.
1. User Merancang BoM untuk Produk Yang Akan Dijual\n
2. User Estimasi Quantity Produksi Yang Akan Dijual\n
3. Finish Goods Terbentuk Dalam Variant Dalam 1 MO\n
    """,
    'category': 'Manufacturing',
    'website': 'https://www.odoo-consultants.com',
    'depends': [
        'base',
        'po_picking_multi_sequence',
        'mrp',
        'purchase',
        'sale',
    ],
    'excludes': ["quality", "quality_mrp"],
    'data': [
        'report/assembly_production_cost_report_templates.xml',
        'report/assembly_production_report_views.xml',
        'report/assembly_plan_cost_report_templates.xml',
        'report/assembly_plan_report_views.xml',
        'report/mrp_production.xml',
        'report/report_assembly_po_production.xml',

        'wizards/vendor_invoice_wizard.xml',
        'wizards/change_vendor_wizard_views.xml',
        'wizards/workorder_extension_wizard_views.xml',
        'wizards/change_inputan_qty_views.xml',
        'wizards/plan_change_vendor_wizard.xml',
        'wizards/product_service_wizard_views.xml',
        'wizards/product_service_remove_wizard_views.xml',
        'wizards/purchase_created_message_wizard_views.xml',

        'security/ir.model.access.csv',

        'data/assembly_sequence.xml',
        'data/stock_picking_type_data.xml',

        'views/res_company_views.xml',
        'views/res_partner_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_move_views.xml',
        'views/product_template_views.xml',

        'views/mrp_bom_views.xml',
        'views/assembly_plan_views.xml',
        'views/purchase_order_views.xml',
        'views/assembly_production_views.xml',
        'views/mrp_production_views.xml',
        'views/mrp_workcenter_views.xml',
        'views/mrp_workorder_views.xml',
    ],
    'demo': [

    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
}
