from odoo.tests.common import tagged
from odoo.tests import TransactionCase


@tagged('at_install', 'post_install')
class TestSaleOrder(TransactionCase):
    """
    Test Sale Order Creation
    """
    def test_001_sale_order_lot(self):
        """
        Test sale order product Lot with product quantity available.
        Check Product Owner stock move line equals to sale order line owner
        :return:
        """
        # set up general data
        location = self.env.ref('stock.stock_location_stock')
        uom = self.env.ref('uom.product_uom_unit').id
        customer = self.env.ref('base.res_partner_1')
        owner = self.env.ref('base.res_partner_2')
        company_id = self.env.company.id

        # set up data product lot
        product_delivery_01 = self.env['product.product'].create({
            'name': 'Product Delivery 01',
            'standard_price': 200.0,
            'list_price': 180.0,
            'type': 'product',
            'uom_id': uom,
            'uom_po_id': uom,
            'default_code': 'DEL_001',
            'tracking': 'lot',
            'company_id': company_id
        })

        # create lot
        lot_01 = self.env['stock.production.lot'].create(
            {'name': 'Lot A 10', 'product_id': product_delivery_01.id,
             'company_id': company_id})

        # update quantity
        self.env['stock.quant']._update_available_quantity(product_delivery_01, location, 10, lot_id=lot_01)
        # get quant
        quant_lot_01 = self.env['stock.quant']._gather(product_delivery_01, location)

        # check quantity lot
        self.assertTrue(quant_lot_01.lot_id, "Lot Exist")
        self.assertEqual(quant_lot_01.quantity, 10)

        # create sale order
        sale_order = self.env['sale.order'].create(
            {'partner_id': customer.id,
             'order_line': [
                 (0, 0, {
                     'name': product_delivery_01.name,
                     'product_id': product_delivery_01.id,
                     'owner_id': owner.id,
                     'product_uom_qty': 5,
                 })]})
        sale_order.action_confirm()

        move_done = sale_order.picking_ids.move_lines[0].move_line_ids[0]
        so_line_owner = sale_order.order_line[0].owner_id

        # check picking
        self.assertTrue(sale_order.picking_ids, "Picking Exist")
        self.assertTrue(len(sale_order.picking_ids), 1)
        self.assertIn('done', sale_order.picking_ids.mapped('move_lines.state'))
        self.assertNotIn('confirmed', sale_order.picking_ids.mapped('move_lines.state'))
        self.assertNotEqual(customer.id, move_done.owner_id.id)
        self.assertEqual(so_line_owner.id, move_done.owner_id.id)

    def test_002_sale_order_lot_unavailable(self):
        """
        Test Sale Order with Product Quantity Unavailable
        :return:
        """
        # set up general data
        location = self.env.ref('stock.stock_location_stock')
        uom = self.env.ref('uom.product_uom_unit').id
        customer = self.env.ref('base.res_partner_1')
        owner = self.env.ref('base.res_partner_2')
        company_id = self.env.company.id

        # set up data product lot
        product_delivery_01 = self.env['product.product'].create({
            'name': 'Product Delivery 01',
            'standard_price': 200.0,
            'list_price': 180.0,
            'type': 'product',
            'uom_id': uom,
            'uom_po_id': uom,
            'default_code': 'DEL_001',
            'tracking': 'lot',
            'company_id': company_id
        })
        # create sale order
        sale_order = self.env['sale.order'].create(
            {'partner_id': customer.id,
             'order_line': [
                 (0, 0, {
                     'name': product_delivery_01.name,
                     'product_id': product_delivery_01.id,
                     'owner_id': owner.id,
                     'product_uom_qty': 5,
                 })]})
        sale_order.action_confirm()
        move_line = sale_order.picking_ids.move_lines[0]
        move_state = sale_order.picking_ids.move_lines.mapped('state')

        # check picking
        self.assertTrue(sale_order.picking_ids, "Picking Exist")
        self.assertTrue(len(sale_order.picking_ids), 1)
        self.assertTrue(not move_line.move_line_ids)
        self.assertIn('confirmed', move_state, "Stock Move State is Confirmed")
        self.assertNotIn('done', move_state, "Stock Move State should not be done")

    def test_003_sale_order_lot_available_non(self):
        """
        Test sale order product Lot with product quantity available and quantity non available.
        Check Product Owner stock move line equals to sale order line owner
        :return:
        """
        # set up general data
        location = self.env.ref('stock.stock_location_stock')
        uom = self.env.ref('uom.product_uom_unit').id
        customer = self.env.ref('base.res_partner_1')
        owner_01 = self.env.ref('base.res_partner_2')
        owner_02 = self.env.ref('base.res_partner_3')
        company_id = self.env.company.id

        # set up data product lot
        # quantity available
        product_delivery_01 = self.env['product.product'].create({
            'name': 'Product Delivery 01',
            'standard_price': 200.0,
            'list_price': 180.0,
            'type': 'product',
            'uom_id': uom,
            'uom_po_id': uom,
            'default_code': 'DEL_001',
            'tracking': 'lot',
            'company_id': company_id
        })
        # quantity unavailable
        product_delivery_02 = self.env['product.product'].create({
            'name': 'Product Delivery 02',
            'standard_price': 200.0,
            'list_price': 180.0,
            'type': 'product',
            'uom_id': uom,
            'uom_po_id': uom,
            'default_code': 'DEL_002',
            'tracking': 'lot',
            'company_id': company_id
        })
        product_delivery_03 = self.env['product.product'].create({
            'name': 'Product Delivery 03',
            'standard_price': 200.0,
            'list_price': 180.0,
            'type': 'product',
            'uom_id': uom,
            'uom_po_id': uom,
            'default_code': 'DEL_003',
            'tracking': 'lot',
            'company_id': company_id
        })

        # create quantity lot available
        lot_01 = self.env['stock.production.lot'].create(
            {'name': 'Lot A 10', 'product_id': product_delivery_01.id,
             'company_id': company_id})

        # update quantity
        self.env['stock.quant']._update_available_quantity(product_delivery_01, location, 10, lot_id=lot_01)
        # get quant
        quant_lot_01 = self.env['stock.quant']._gather(product_delivery_01, location)

        # check quantity lot
        self.assertTrue(quant_lot_01.lot_id, "Lot Exist")
        self.assertEqual(sum(quant_lot_01.mapped('quantity')), 10)

        # create sale order with 2 owner
        sale_order = self.env['sale.order'].create(
            {'partner_id': customer.id,
             'order_line': [
                 (0, 0, {
                     'name': product_delivery_01.name,
                     'product_id': product_delivery_01.id,
                     'owner_id': owner_01.id,
                     'product_uom_qty': 5,
                 }),
                 (0, 0, {
                     'name': product_delivery_02.name,
                     'product_id': product_delivery_02.id,
                     'owner_id': owner_02.id,
                     'product_uom_qty': 5,
                 }),
                 (0, 0, {
                     'name': product_delivery_03.name,
                     'product_id': product_delivery_03.id,
                     'product_uom_qty': 5,
                 })
             ]})
        sale_order.action_confirm()
        # check length picking
        self.assertTrue(sale_order.picking_ids, "Picking Exist")
        self.assertGreater(len(sale_order.picking_ids), 1, "Total picking should be greater than 1")

        sol_lot_owner_available = sale_order.order_line[0].owner_id

        # stock move quantity available
        move_done = sale_order.picking_ids[0].mapped('move_lines')
        mvl_owner_available = move_done.move_line_ids.mapped('owner_id')
        # stock move quantity unavailable
        move_todo = sale_order.picking_ids[1].mapped('move_lines')

        # check sale order line owner equals to move line owner > quantity available
        self.assertEquals(sol_lot_owner_available.id, mvl_owner_available.id, "owner should be consistent")
        # check move line quantity unavailable
        self.assertTrue(not move_todo.move_line_ids, "Move Line should no be created")
        # check stock move quantity available
        self.assertIn('done', move_done.mapped('state'), "Quantity Available")
        # check stock move quantity unavailable
        self.assertNotIn('done', move_todo.mapped('state'), "Quantity Unavailable")

    def test_004_sale_order_lot_available_serial(self):
        """
        Test sale order product Lot with product quantity available and product serial with quantity available.
        Check Product Owner stock move line equals to sale order line owner
        :return:
        """
        # set up general data
        location = self.env.ref('stock.stock_location_stock')
        uom = self.env.ref('uom.product_uom_unit').id
        customer = self.env.ref('base.res_partner_1')
        owner_01 = self.env.ref('base.res_partner_2')
        owner_02 = self.env.ref('base.res_partner_3')
        company_id = self.env.company.id

        # set up data product lot
        # quantity available
        product_delivery_01 = self.env['product.product'].create({
            'name': 'Product Delivery 01',
            'standard_price': 200.0,
            'list_price': 180.0,
            'type': 'product',
            'uom_id': uom,
            'uom_po_id': uom,
            'default_code': 'DEL_001',
            'tracking': 'lot',
            'company_id': company_id
        })
        # quantity available serial
        product_delivery_02 = self.env['product.product'].create({
            'name': 'Product Delivery 02',
            'standard_price': 200.0,
            'list_price': 180.0,
            'type': 'product',
            'uom_id': uom,
            'uom_po_id': uom,
            'default_code': 'DEL_002',
            'tracking': 'serial',
            'company_id': company_id
        })

        # create quantity lot available
        lot_01 = self.env['stock.production.lot'].create(
            {'name': 'Lot A 10',
             'product_id': product_delivery_01.id,
             'company_id': company_id
             })
        # A serial number should only be linked to a single product
        serial_01 = self.env['stock.production.lot'].create(
            {'name': 'Serial A',
             'product_id': product_delivery_02.id,
             'company_id': company_id
             })
        serial_02 = self.env['stock.production.lot'].create(
            {'name': 'Serial B',
             'product_id': product_delivery_02.id,
             'company_id': company_id
             })

        # update quantity
        self.env['stock.quant']._update_available_quantity(product_delivery_01, location, 10, lot_id=lot_01)
        self.env['stock.quant']._update_available_quantity(product_delivery_02, location, 1, lot_id=serial_01)
        self.env['stock.quant']._update_available_quantity(product_delivery_02, location, 1, lot_id=serial_02)

        # get quant
        quant_lot_01 = self.env['stock.quant']._gather(product_delivery_01, location)
        quant_serial_0102 = self.env['stock.quant']._gather(product_delivery_02, location)

        # check quantity lot
        self.assertTrue(quant_lot_01.lot_id, "Lot Exist")
        self.assertEqual(sum(quant_lot_01.mapped('quantity')), 10)

        self.assertGreater(len(quant_serial_0102), 1, "The serial number should be 2")
        self.assertTrue(quant_serial_0102.lot_id, "Serial Exist")
        self.assertEqual(sum(quant_serial_0102.mapped('quantity')), 2)

        # create sale order
        sale_order = self.env['sale.order'].create(
            {'partner_id': customer.id,
             'order_line': [
                 (0, 0, {
                     'name': product_delivery_01.name,
                     'product_id': product_delivery_01.id,
                     'owner_id': owner_01.id,
                     'product_uom_qty': 5,
                 }),
                 (0, 0, {
                     'name': product_delivery_02.name,
                     'product_id': product_delivery_02.id,
                     'owner_id': owner_02.id,
                     'product_uom_qty': 2,
                 })
             ]})
        sale_order.action_confirm()
        # check picking
        self.assertTrue(sale_order.picking_ids, "Picking Exist")
        # check total picking created
        self.assertEqual(len(sale_order.picking_ids), 1, "Total Picking should be 1")

        sol_lot_owner = sale_order.order_line[0].owner_id
        sol_serial_owner = sale_order.order_line[1].owner_id
        move_done = sale_order.picking_ids[0].mapped('move_lines')
        mvl_lot_owner = sale_order.picking_ids[0].move_lines[0].move_line_ids[0].mapped('owner_id')
        mvl_serial_owner = sale_order.picking_ids[0].move_lines[1].move_line_ids[1].mapped('owner_id')

        # check quantity available
        self.assertIn('done', move_done.mapped('state'), "Quantity Available")
        self.assertNotIn('confirmed', move_done.mapped('state'), "Picking state should be done")
        # check owner move line success
        self.assertEquals(sol_lot_owner.id, mvl_lot_owner.id, "Lot Owner should be consistent")
        self.assertEquals(sol_serial_owner.id, mvl_serial_owner.id, "Serial owner should be consistent")
        # check owner move line fail
        self.assertNotEquals(sol_serial_owner.id, mvl_lot_owner.id, "Lot Owner should not be consistent")
        self.assertNotEquals(sol_lot_owner.id, mvl_serial_owner.id, "Serial owner should not be consistent")

    def test_005_sale_order_qty_available(self):
        """
        Test sale order product with product quantity available.
        Check Product Owner stock move line equals to sale order line owner
        :return:
        """
        # set up general data
        location = self.env.ref('stock.stock_location_stock')
        uom = self.env.ref('uom.product_uom_unit').id
        customer = self.env.ref('base.res_partner_1')
        owner_01 = self.env.ref('base.res_partner_2')
        owner_02 = self.env.ref('base.res_partner_3')
        owner_03 = self.env.ref('base.res_partner_4')
        company_id = self.env.company.id

        # set up data product lot
        product_delivery_01 = self.env['product.product'].create({
            'name': 'Product Delivery 01',
            'standard_price': 200.0,
            'list_price': 180.0,
            'type': 'product',
            'uom_id': uom,
            'uom_po_id': uom,
            'default_code': 'DEL_001',
            'company_id': company_id
        })
        product_delivery_02 = self.env['product.product'].create({
            'name': 'Product Delivery 02',
            'standard_price': 200.0,
            'list_price': 180.0,
            'type': 'product',
            'uom_id': uom,
            'uom_po_id': uom,
            'default_code': 'DEL_002',
            'company_id': company_id
        })
        product_delivery_03 = self.env['product.product'].create({
            'name': 'Product Delivery 03',
            'standard_price': 200.0,
            'list_price': 180.0,
            'type': 'product',
            'uom_id': uom,
            'uom_po_id': uom,
            'default_code': 'DEL_003',
            'company_id': company_id
        })

        # update quantity
        self.env['stock.quant']._update_available_quantity(product_delivery_01, location, 10)
        self.env['stock.quant']._update_available_quantity(product_delivery_02, location, 10)
        self.env['stock.quant']._update_available_quantity(product_delivery_03, location, 10)

        # create sale order
        sale_order = self.env['sale.order'].create(
            {'partner_id': customer.id,
             'order_line': [
                 (0, 0, {
                     'name': product_delivery_01.name,
                     'product_id': product_delivery_01.id,
                     'owner_id': owner_01.id,
                     'product_uom_qty': 5,
                 }),
                 (0, 0, {
                     'name': product_delivery_02.name,
                     'product_id': product_delivery_02.id,
                     'owner_id': owner_02.id,
                     'product_uom_qty': 5,
                 }),
                 (0, 0, {
                     'name': product_delivery_03.name,
                     'product_id': product_delivery_03.id,
                     'owner_id': owner_03.id,
                     'product_uom_qty': 5,
                 })
             ]})
        sale_order.action_confirm()

        # check picking
        self.assertTrue(sale_order.picking_ids)
        self.assertEqual(len(sale_order.picking_ids),  1)

        # compare owner sale order line and stock move line owner
        sol_owner = [sol.id for sol in sale_order.mapped('order_line.owner_id')]
        mvl_owner = [mvl.id for mvl in sale_order.picking_ids.mapped('move_lines.move_line_ids').mapped('owner_id')]
        self.assertGreater(len(sale_order.picking_ids.mapped('move_lines')), 1)
        self.assertItemsEqual(sol_owner, mvl_owner)

    def test_006_sale_order(self):
        """
        Test sale order product with product quantity available.
        Product type consu, service, product
        Check Product Owner stock move line equals to sale order line owner
        :return:
        """
        # set up general data
        location = self.env.ref('stock.stock_location_stock')
        uom = self.env.ref('uom.product_uom_unit').id
        customer = self.env.ref('base.res_partner_1')
        owner_01 = self.env.ref('base.res_partner_2')
        owner_02 = self.env.ref('base.res_partner_3')
        owner_03 = self.env.ref('base.res_partner_4')
        company_id = self.env.company.id

        # set up data product
        product_delivery_01 = self.env['product.product'].create({
            'name': 'Product Delivery 01',
            'standard_price': 200.0,
            'list_price': 180.0,
            'type': 'product',
            'uom_id': uom,
            'uom_po_id': uom,
            'default_code': 'DEL_001',
            'company_id': company_id
        })
        product_delivery_02 = self.env['product.product'].create({
            'name': 'Product Delivery 02',
            'standard_price': 200.0,
            'list_price': 180.0,
            'type': 'consu',
            'uom_id': uom,
            'uom_po_id': uom,
            'default_code': 'DEL_002',
            'company_id': company_id
        })
        product_delivery_03 = self.env['product.product'].create({
            'name': 'Product Delivery 03',
            'standard_price': 200.0,
            'list_price': 180.0,
            'type': 'service',
            'uom_id': uom,
            'uom_po_id': uom,
            'default_code': 'DEL_003',
            'company_id': company_id
        })

        # update quantity product storable
        self.env['stock.quant']._update_available_quantity(product_delivery_01, location, 10)

        # create sale order
        sale_order = self.env['sale.order'].create(
            {'partner_id': customer.id,
             'order_line': [
                 (0, 0, {
                     'name': product_delivery_01.name,
                     'product_id': product_delivery_01.id,
                     'owner_id': owner_01.id,
                     'product_uom_qty': 5,
                 }),
                 (0, 0, {
                     'name': product_delivery_02.name,
                     'product_id': product_delivery_02.id,
                     'owner_id': owner_02.id,
                     'product_uom_qty': 5,
                 }),
                 (0, 0, {
                     'name': product_delivery_03.name,
                     'product_id': product_delivery_03.id,
                     'owner_id': owner_03.id,
                     'product_uom_qty': 5,
                 })
             ]})
        sale_order.action_confirm()

        # check picking
        self.assertTrue(sale_order.picking_ids)
        self.assertEqual(len(sale_order.picking_ids),  1)

        # compare owner sale order line and stock move line owner
        sol_owner = [
            sol.id
            for sol in sale_order.order_line.filtered(
                lambda x: x.product_type != 'service').mapped('owner_id')]
        mvl_owner = [mvl.id for mvl in sale_order.picking_ids.mapped('move_lines.move_line_ids').mapped('owner_id')]
        self.assertGreater(len(sale_order.picking_ids.mapped('move_lines')), 1)
        self.assertItemsEqual(sol_owner, mvl_owner)


