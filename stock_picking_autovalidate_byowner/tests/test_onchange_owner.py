from odoo.tests.common import tagged
from odoo.tests import TransactionCase


@tagged('-at_install', 'post_install')
class TestOnchangeOwnerId(TransactionCase):
    """
    Test Onchange Product Owner
    """
    def test_onchange_owner_id(self):
        """
        Test Onchange Product Owner
        :return:
        """
        uom_id = self.env.ref('uom.product_uom_unit').id

        customer_id = self.env.ref('base.res_partner_1')
        owner_id = self.env.ref('base.res_partner_2')

        product_01 = self.env['product.product'].create({
            'name': 'Product Delivery 01',
            'standard_price': 200.0,
            'list_price': 180.0,
            'type': 'product',
            'uom_id': uom_id,
            'uom_po_id': uom_id,
            'default_code': 'DEL_001',
            'company_id': self.env.company.id
        })
        product_01.write(
            {'seller_ids': [(0, 0, {'name': owner_id.id, 'company_id': self.env.company.id})]})

        # check product vendor
        self.assertTrue(product_01.seller_ids, 'Vendor Exist')
        self.assertEquals(owner_id.id, product_01.seller_ids.mapped('name').id, "Vendor is consistent")

        # create sale order
        sale_order = self.env['sale.order'].create({
            'partner_id': customer_id.id,
            'order_line': [
                (0, 0, {'name': product_01.name, 'product_id': product_01.id, 'product_uom_qty': 5})
            ]
        })
        # onchange
        sale_order.order_line[0].product_id_change()
        self.assertEquals(owner_id.id, sale_order.order_line[0].owner_id.id, "Sale Order Line Owner is Consistent")
