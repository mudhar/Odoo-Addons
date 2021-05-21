from odoo import fields, models, _


class ProductMargin(models.TransientModel):
    """
    Inherit model product.margin change display name action windows
    """
    _inherit = 'product.margin'
    _description = 'Product Margin'

    def action_open_window(self):
        """
        update result name to date input
        :return:dict
        """
        result = super(ProductMargin, self).action_open_window()
        # format date
        from_date = fields.Date.from_string(self.from_date).strftime('%m/%d/%Y')
        to_date = fields.Date.from_string(self.to_date).strftime('%m/%d/%Y')
        result.update({
            'name': _("Product Margins %s - %s") % (from_date, to_date)
        })
        return result
