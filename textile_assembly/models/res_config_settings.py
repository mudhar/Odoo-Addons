from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_operation_type_consume_id = fields.Many2one(comodel_name="stock.picking.type", string="Operation Type Consume")
    default_operation_type_produce_id = fields.Many2one(comodel_name="stock.picking.type", string="Operation Type Produce")

    location_id = fields.Many2one(comodel_name="stock.location", string="Location Stock")
    service_categ_id = fields.Many2one(comodel_name="product.category", string="Set Kategor Produk Jasa")

    module_mrp_daily_report = fields.Boolean(string="Mrp Daily Report")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        IrDefault = self.env['ir.default'].sudo()
        operation_type_consume_id = IrDefault.get('mrp.production', "picking_type_consume",
                                                  company_id=self.env.user.company_id.id)

        operation_type_produce_id = IrDefault.get('mrp.production', "picking_type_production",
                                                  company_id=self.env.user.company_id.id)

        location_id = IrDefault.get('assembly.plan', "location_id", company_id=self.env.user.company_id.id)
        service_categ_id = IrDefault.get('mrp.workorder', "service_categ_id", company_id=self.env.user.company_id.id)

        res.update(
            default_operation_type_consume_id=operation_type_consume_id if operation_type_consume_id else False,
            default_operation_type_produce_id=operation_type_produce_id if operation_type_produce_id else False,
            location_id=location_id if location_id else False,
            service_categ_id=service_categ_id if service_categ_id else False
        )
        return res

    @api.multi
    def set_values(self):
        IrDefault = self.env['ir.default']
        if self.default_operation_type_consume_id:
            IrDefault.sudo().set('mrp.production', "picking_type_consume", self.default_operation_type_consume_id.id,
                                 company_id=self.env.user.company_id.id)
        if self.default_operation_type_produce_id:
            IrDefault.sudo().set('mrp.production', "picking_type_production", self.default_operation_type_produce_id.id,
                                 company_id=self.env.user.company_id.id)
        if self.location_id:
            IrDefault.sudo().set('assembly.plan', "location_id", self.location_id.id,
                                 company_id=self.env.user.company_id.id)
        if self.service_categ_id:
            IrDefault.sudo().set('mrp.workorder', "service_categ_id", self.service_categ_id.id,
                                 company_id=self.env.user.company_id.id)
        return super(ResConfigSettings, self).set_values()

